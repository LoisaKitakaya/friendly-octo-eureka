import uuid
from django.db import models
from users.models import User
from products.models import Product


class Order(models.Model):
    """Tracks customer purchases"""

    PENDING = "Pending"
    PROCESSING = "Processing"
    SHIPPED = "Shipped"
    DELIVERED = "Delivered"
    CANCELED = "Canceled"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (PROCESSING, "Processing"),
        (SHIPPED, "Shipped"),
        (DELIVERED, "Delivered"),
        (CANCELED, "Canceled"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
    )
    total_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0, # type: ignore
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Buyer Order"
        verbose_name_plural = "Buyer Orders"

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


class OrderItem(models.Model):
    """Products within an order"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="order_items",
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Buyer Order Item"
        verbose_name_plural = "Buyer Order Items"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
