# from decimal import Decimal
# from django.conf import settings
# from django.db import models

# # Create your models here.





# class Cart(models.Model):
#     user = models.OneToOneField(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.CASCADE,
#         related_name="cart",
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     @property
#     def subtotal(self):
#         return sum((item.line_total for item in self.items.all()), Decimal("0.00"))

#     def __str__(self):
#         return f"Cart - {self.user.username}"


# class CartItem(models.Model):
#     cart = models.ForeignKey(
#         Cart,
#         on_delete=models.CASCADE,
#         related_name="items",
#     )
#     product = models.ForeignKey(
#         "store.Product",
#         on_delete=models.CASCADE,
#         related_name="cart_items",
#     )
#     quantity = models.PositiveIntegerField(default=1)

#     class Meta:
#         unique_together = ("cart", "product")

#     @property
#     def unit_price(self):
#         return self.product.price

#     @property
#     def line_total(self):
#         return self.product.price * self.quantity

#     def __str__(self):
#         return f"{self.product} x {self.quantity}"
