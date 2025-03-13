import uuid
import stripe
from celery import shared_task
from django.conf import settings
from products.models import Product
from orders.models import OrderItem
from users.models import ArtistProfile


@shared_task
def _create_product(product_id: uuid.UUID, **kwargs) -> None:
    """Create a new product on Stripe"""

    try:
        user_id = kwargs.get("user_id")

        if user_id:
            artist_profile = ArtistProfile.objects.get(user__id=user_id)

            if artist_profile.decrypt_secret_key() is None:
                raise Exception("Missing Stripe secret key for artist store")

            stripe.api_key = artist_profile.decrypt_secret_key()

        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY

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
def _update_product(product_id: uuid.UUID, **kwargs) -> None:
    """Update a product on stripe"""

    try:
        user_id = kwargs.get("user_id")

        if user_id:
            artist_profile = ArtistProfile.objects.get(user__id=user_id)

            if artist_profile.decrypt_secret_key() is None:
                raise Exception("Missing Stripe secret key for artist store")

            stripe.api_key = artist_profile.decrypt_secret_key()

        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY

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


def create_payment_link(order_id: uuid.UUID, **kwargs) -> dict:
    """Create a payment link"""

    try:
        user_id = kwargs.get("user_id")

        if user_id:
            artist_profile = ArtistProfile.objects.get(user__id=user_id)

            if artist_profile.decrypt_secret_key() is None:
                raise Exception("Missing Stripe secret key for artist store")

            stripe.api_key = artist_profile.decrypt_secret_key()

        else:
            stripe.api_key = settings.STRIPE_SECRET_KEY

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
        stripe.api_key = settings.STRIPE_SECRET_KEY

        stripe.WebhookEndpoint.create(
            enabled_events=[
                "charge.succeeded",
                "charge.failed",
            ],
            url=f"{settings.BACKEND_URL}/api/v1/orders/payment-event-callback",
        )
    except Exception as e:
        raise Exception(f"Error creating webhook: {e}")
