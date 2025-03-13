from typing import List, Literal
from ninja import Schema, ModelSchema
from orders.models import Order, OrderItem
from users.api.v1.schema import UserSchema
from products.api.v1.schema import ProductSchema


class OrderSchema(ModelSchema):
    class Meta:
        model = Order
        fields = "__all__"
        depth = 1

    user: UserSchema


class OrderItemSchema(ModelSchema):
    class Meta:
        model = OrderItem
        fields = "__all__"
        depth = 1

    product: ProductSchema


class OrderStatusSchema(Schema):
    shipping_status: Literal["pending", "shipped", "delivered", "canceled"]


class OrderItemInputSchema(Schema):
    product_id: str
    quantity: int
    price: float


class OrderInputSchema(Schema):
    items: List[OrderItemInputSchema]
