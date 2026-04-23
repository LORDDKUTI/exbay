# from decimal import Decimal
# from django.conf import settings
# from django.db import models
# # Create your models here.






from django.urls import path
from .views import orders_home

urlpatterns = [
    path("", orders_home, name="orders-home"),
]

# class Order(models.Model):
#     PENDING = "pending"
#     PAID = "paid"
#     CANCELLED = "cancelled"
#     FULFILLED = "fulfilled"

#     STATUS_CHOICES = [
#         (PENDING, "Pending"),
#         (PAID, "Paid"),
#         (CANCELLED, "Cancelled"),
#         (FULFILLED, "Fulfilled"),
#     ]

#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="orders",
#     )
#     shipping_address = models.ForeignKey(
#         "accounts.Address",
#         on_delete=models.PROTECT,
#         related_name="shipping_orders",
#     )
#     billing_address = models.ForeignKey(
#         "accounts.Address",
#         on_delete=models.PROTECT,
#         related_name="billing_orders",
#         null=True,
#         blank=True,
#     )

#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

#     subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
#     tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
#     shipping_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
#     total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"Order #{self.pk} - {self.user.username}"


# class OrderItem(models.Model):
#     order = models.ForeignKey(
#         Order,
#         on_delete=models.CASCADE,
#         related_name="items",
#     )
#     product = models.ForeignKey(
#         "store.Product",
#         on_delete=models.PROTECT,
#         related_name="order_items",
#     )
#     product_name = models.CharField(max_length=255)
#     unit_price = models.DecimalField(max_digits=12, decimal_places=2)
#     quantity = models.PositiveIntegerField(default=1)
#     line_total = models.DecimalField(max_digits=12, decimal_places=2)

#     def __str__(self):
#         return f"OrderItem {self.product_name} x {self.quantity}"
