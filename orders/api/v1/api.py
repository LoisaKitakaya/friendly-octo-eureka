import json
import stripe
from ninja import Router
from django.conf import settings
from products.models import Product
from orders.models import Order, OrderItem
from utils.notifications import send_email
from utils.stripe import create_payment_link
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.base import (
    parse_uuid,
    AuthBearer,
    require_active,
    get_authenticated_user,
)
from .schema import OrderInputSchema

router = Router()

bearer = AuthBearer()

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SIGNING_KEY


@router.post("/create-order", auth=bearer, response=dict)
@require_active
def create_order(request, data: OrderInputSchema):
    user = get_authenticated_user(request)

    order = Order.objects.create(user=user)

    for item in data.items:
        product = Product.objects.get(id=parse_uuid(item.product_id))

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item.quantity,
            price=item.price,
        )

    order.total_price = sum((item.price * item.quantity) for item in data.items)

    order.save()

    payment_url = create_payment_link(order.id)

    order_url = f"{settings.BACKEND_URL}/admin/orders/order/{order.id}/change/"

    subject = "New Order Created"

    message = f"A new order has been created: {order_url}"

    send_email.delay(
        subject=subject,
        message=message,
        receiver_email_address=settings.ADMIN_PERSONAL_EMAIL,
    )

    return {
        "message": "Order created successfully",
        "payment_url": payment_url.get("payment_url"),
    }


@router.post("/payment-event-callback")
@csrf_exempt
def payment_event_callback(request):
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    payload = request.body

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            endpoint_secret,
        )
    except ValueError:
        return JsonResponse({"error": "Invalid payload"}, status=400)
    except stripe.SignatureVerificationError:
        return JsonResponse({"error": "Invalid signature"}, status=400)

    event_type = event["type"]
    session = event["data"]["object"]
    order_id = session.get("metadata", {}).get("order_id")

    if not order_id:
        print("⚠️ No order_id found in metadata")
        
        return HttpResponse(status=400)

    try:
        order = Order.objects.get(id=parse_uuid(order_id))
    except Order.DoesNotExist:
        print(f"⚠️ Order {order_id} not found!")
        
        return HttpResponse(status=400)

    # ✅ Handling completed sessions
    if event_type == "checkout.session.completed":
        payment_status = session.get("payment_status")

        if payment_status == "paid":  # Instant payments (cards, etc.)
            order.payment_status = Order.PAID
            order.shipping_status = Order.PROCESSING
            
            order.save()

            print(f"✅ Order {order.id} marked as PAID and PROCESSING")

            send_email.delay(
                subject="Order Payment Successful",
                message=f"Your order {order.id} has been paid successfully!",
                receiver_email_address=order.user.email,
            )
        else:
            print(f"⏳ Order {order.id} payment is still pending...")

    # ✅ Handling async payments that later succeed
    elif event_type == "checkout.session.async_payment_succeeded":
        order.payment_status = Order.PAID
        order.shipping_status = Order.PROCESSING
        
        order.save()

        print(f"✅ Async Payment for Order {order.id} marked as PAID")

        send_email.delay(
            subject="Order Payment Successful",
            message=f"Your order {order.id} has been paid successfully!",
            receiver_email_address=order.user.email,
        )

    # ❌ Handling failed async payments
    elif event_type == "checkout.session.async_payment_failed":
        order.payment_status = Order.NOT_PAID
        order.shipping_status = Order.CANCELED
        
        order.save()

        print(f"❌ Async Payment for Order {order.id} failed and marked as CANCELED")

        send_email.delay(
            subject="Order Payment Failed",
            message=f"Your payment for order {order.id} has failed.",
            receiver_email_address=order.user.email,
        )

    else:
        print(f"Unhandled event: {event_type}")

    return HttpResponse(status=200)
