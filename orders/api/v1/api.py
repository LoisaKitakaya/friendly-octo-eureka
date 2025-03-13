from ninja import Router
from products.models import Product
from orders.models import Order, OrderItem
from utils.stripe import create_payment_link
from utils.base import (
    parse_uuid,
    AuthBearer,
    require_active,
    get_authenticated_user,
)
from .schema import OrderInputSchema

router = Router()

bearer = AuthBearer()


@router.get("/create-order", auth=bearer, response=dict)
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

    payment_url = create_payment_link(order)

    return {
        "message": "Order created successfully",
        "payment_url": payment_url,
    }
