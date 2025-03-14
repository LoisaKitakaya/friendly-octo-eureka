import stripe
from celery import shared_task
from django.conf import settings
from utils.base import parse_uuid
from products.models import Product
from orders.models import OrderItem
from users.models import ArtistProfile


stripe.api_key = settings.STRIPE_SECRET_KEY


@shared_task
def _create_product(product_id: str) -> None:
    """Create a new product on Stripe"""

    product_id = parse_uuid(product_id)  # type: ignore

    try:
        product = Product.objects.get(id=product_id)

        stripe_product = stripe.Product.create(
            name=product.name,
            description=product.description,
            images=[product.image.url],
        )

        stripe_price = stripe.Price.create(
            currency="usd",
            unit_amount=int(product.price) * 100,
            product=stripe_product.id,
        )

        product.stripe_product_id = stripe_product.id
        product.stripe_price_id = stripe_price.id

        product.save()
    except Exception as e:
        raise Exception(f"Error creating product on Stripe: {e}")


@shared_task
def _update_product(product_id: str) -> None:
    """Update a product on stripe"""

    product_id = parse_uuid(product_id)  # type: ignore

    try:
        product = Product.objects.get(id=product_id)

        stripe_product = stripe.Product.modify(
            str(product.stripe_product_id),
            name=product.name,
            description=product.description,
            images=[product.image.url],
        )

        stripe_price = stripe.Price.create(
            currency="usd",
            unit_amount=int(product.price) * 100,
            product=stripe_product.id,
        )

        product.stripe_price_id = stripe_price.id

        product.save()
    except Exception as e:
        raise Exception(f"Error updating product on Stripe: {e}")


def create_payment_link(order_id: str) -> dict:
    """Create a payment link"""

    order_id = parse_uuid(order_id)  # type: ignore

    try:
        order_items = OrderItem.objects.filter(order__id=order_id)

        stripe_payment_link = stripe.PaymentLink.create(
            line_items=[
                {
                    "price": str(order_item.product.stripe_price_id),
                    "quantity": order_item.quantity,
                }
                for order_item in order_items
            ],
            metadata={"order_id": str(order_id)},
        )

        return {"payment_url": stripe_payment_link.url}
    except Exception as e:
        raise Exception(f"Error creating payment link: {e}")


def create_payment_event_webhook() -> None:
    try:
        stripe.WebhookEndpoint.create(
            enabled_events=[
                "charge.succeeded",
                "charge.failed",
            ],
            url=f"{settings.BACKEND_URL}/api/v1/orders/payment-event-callback",
        )
    except Exception as e:
        raise Exception(f"Error creating webhook: {e}")
