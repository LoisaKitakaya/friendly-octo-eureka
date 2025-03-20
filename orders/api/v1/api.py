import stripe
from ninja import Router
from django.conf import settings
from products.models import Product
from .schema import OrderStatusSchema
from users.models import ArtistProfile
from orders.models import Order, OrderItem
from utils.notifications import send_email
from utils.stripe import create_payment_link
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.base import (
    parse_uuid,
    AuthBearer,
    require_role,
    require_active,
    get_authenticated_user,
)
from .schema import OrderInputSchema

router = Router()

bearer = AuthBearer()

stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SIGNING_KEY


@router.get("/user-orders", auth=bearer, response=dict)
@require_active
@require_role(is_artist=False)
def get_all_user_orders(request):
    user = get_authenticated_user(request)

    orders = Order.objects.filter(user=user).order_by("-created_at")

    results = [
        {
            "id": str(order.id),
            "payment_status": order.payment_status,
            "shipping_status": order.shipping_status,
            "total_price": float(order.total_price),
            "created_at": order.created_at.isoformat(),
            "items": [
                {
                    "product_id": str(item.product.id),
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "name": item.product.name,
                }
                for item in order.items.all()  # type: ignore
            ],
        }
        for order in orders
    ]

    return {"orders": results}


@router.get("/seller-orders", auth=bearer, response=dict)
@require_active
@require_role(is_artist=True)
def get_all_seller_orders(request):
    user = get_authenticated_user(request)

    artist_profile = ArtistProfile.objects.get(user=user)

    orders = (
        Order.objects.filter(
            items__product__artist=artist_profile,
        )
        .distinct()
        .order_by("-created_at")
    )

    results = []
    for order in orders:
        seller_items = [
            {
                "product_id": str(item.product.id),
                "quantity": item.quantity,
                "price": float(item.price),
                "name": item.product.name,
            }
            for item in order.items.all()  # type: ignore
            if item.product.artist == artist_profile
        ]
        
        results.append(
            {
                "id": str(order.id),
                "payment_status": order.payment_status,
                "shipping_status": order.shipping_status,
                "total_price": float(order.total_price),
                "created_at": order.created_at.isoformat(),
                "items": seller_items,
            }
        )

    return {"orders": results}


@router.put("/user-orders/{order_id}", auth=bearer, response=dict)
@require_active
@require_role(is_artist=True)
def update_user_order(request, order_id: str, data: OrderStatusSchema):
    order = Order.objects.get(id=parse_uuid(order_id))

    order.shipping_status = data.shipping_status

    order.save()

    return {"message": "Order status updated successfully"}


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

    payment_url = create_payment_link(str(order.id))

    # Notify Admin about the new order
    order_admin_url = f"{settings.BACKEND_URL}/admin/orders/order/{order.id}/change/"

    send_email.delay(
        subject="New Order Created",
        message=f"A new order has been created: {order_admin_url}",
        receiver_email_address=settings.ADMIN_PERSONAL_EMAIL,
    )

    # Notify the seller(s): get unique seller emails from order items
    seller_emails = {item.product.artist.user.email for item in order.items.all()} # type: ignore

    seller_dashboard_url = f"{settings.SELLER_FRONTEND_URL}/store/orders"

    seller_subject = "New Order Created"
    seller_message = f"A new order has been created. Please check your dashboard: {seller_dashboard_url}"

    for email in seller_emails:
        send_email.delay(
            subject=seller_subject,
            message=seller_message,
            receiver_email_address=email,
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
        # print("⚠️ No order_id found in metadata")

        return HttpResponse(status=400)

    try:
        order = Order.objects.get(id=parse_uuid(order_id))
    except Order.DoesNotExist:
        # print(f"⚠️ Order {order_id} not found!")

        return HttpResponse(status=400)

    # ✅ Handling completed sessions
    if event_type == "checkout.session.completed":
        payment_status = session.get("payment_status")

        if payment_status == "paid":  # Instant payments (cards, etc.)
            order.payment_status = Order.PAID
            order.shipping_status = Order.PROCESSING

            order.save()

            for item in order.items.all():  # type: ignore
                item.product.stock -= item.quantity

                item.product.save()

            # print(f"✅ Order {order.id} marked as PAID and PROCESSING")

            # Notify buyer that payment was successful
            send_email.delay(
                subject="Order Payment Successful",
                message=f"Your order {order.id} has been paid successfully!",
                receiver_email_address=order.user.email,
            )

            # Notify admin
            order_admin_url = (
                f"{settings.BACKEND_URL}/admin/orders/order/{order.id}/change/"
            )

            send_email.delay(
                subject="Order Payment Successful",
                message=f"Order Payment Successful: {order_admin_url}",
                receiver_email_address=settings.ADMIN_PERSONAL_EMAIL,
            )

            # Notify seller(s)
            seller_emails = {
                item.product.artist.user.email for item in order.items.all() # type: ignore
            }

            seller_dashboard_url = f"{settings.SELLER_FRONTEND_URL}/store/orders"

            seller_subject = "Order Payment Successful"
            seller_message = f"Order Payment Successful: Please check your orders dashboard: {seller_dashboard_url}"

            for email in seller_emails:
                send_email.delay(
                    subject=seller_subject,
                    message=seller_message,
                    receiver_email_address=email,
                )
        else:
            # print(f"⏳ Order {order.id} payment is still pending...")

            pass

    # ✅ Handling async payments that later succeed
    elif event_type == "checkout.session.async_payment_succeeded":
        order.payment_status = Order.PAID
        order.shipping_status = Order.PROCESSING

        order.save()

        # print(f"✅ Async Payment for Order {order.id} marked as PAID")

        # Notify buyer that async payment was successful
        send_email.delay(
            subject="Order Payment Successful",
            message=f"Your order {order.id} has been paid successfully!",
            receiver_email_address=order.user.email,
        )

        # Notify admin
        order_admin_url = (
            f"{settings.BACKEND_URL}/admin/orders/order/{order.id}/change/"
        )

        send_email.delay(
            subject="Order Payment Successful",
            message=f"Order Payment Successful: {order_admin_url}",
            receiver_email_address=settings.ADMIN_PERSONAL_EMAIL,
        )

        # Notify seller(s)
        seller_emails = {item.product.artist.user.email for item in order.items.all()} # type: ignore

        seller_dashboard_url = f"{settings.SELLER_FRONTEND_URL}/store/orders"

        seller_subject = "Order Payment Successful"
        seller_message = f"Order Payment Successful: Please check your orders dashboard: {seller_dashboard_url}"

        for email in seller_emails:
            send_email.delay(
                subject=seller_subject,
                message=seller_message,
                receiver_email_address=email,
            )

    # ❌ Handling failed async payments
    elif event_type == "checkout.session.async_payment_failed":
        order.payment_status = Order.NOT_PAID
        order.shipping_status = Order.CANCELED

        order.save()

        # print(f"❌ Async Payment for Order {order.id} failed and marked as CANCELED")

        # Notify buyer about payment failure
        send_email.delay(
            subject="Order Payment Failed",
            message=f"Your payment for order {order.id} has failed.",
            receiver_email_address=order.user.email,
        )

    else:
        # print(f"Unhandled event: {event_type}")

        pass

    return HttpResponse(status=200)
