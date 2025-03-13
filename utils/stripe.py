import stripe
from django.conf import settings
from products.models import Product
from orders.models import Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


def _create_product(product: Product) -> dict:
    """Create a new product on Stripe"""

    try:
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

        return {
            "stripe_product_id": stripe_product.id,
            "stripe_price_id": stripe_price.id,
        }
    except Exception as e:
        raise Exception(f"Error creating product on Stripe: {e}")


def _update_product(product: Product) -> dict:
    """Update a product on stripe"""

    try:
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

        return {"stripe_price_id": stripe_price.id}
    except Exception as e:
        raise Exception(f"Error updating product on Stripe: {e}")


def create_payment_link(order: Order) -> dict:
    """Create a payment link"""

    order_items = OrderItem.objects.filter(order=order)

    try:
        stripe_payment_link = stripe.PaymentLink.create(
            line_items=[
                {
                    "price": str(order_item.product.stripe_price_id),
                    "quantity": order_item.quantity,
                }
                for order_item in order_items
            ],
        )

        return {"payment_url": stripe_payment_link.url}
    except Exception as e:
        raise Exception(f"Error creating payment link: {e}")
