

# from decimal import Decimal
# from django.db import transaction

# from accounts.models import Address
# from cart.models import Cart
# from orders.models import Order, OrderItem


# def calculate_tax(subtotal):
#     return subtotal * Decimal("0.00")


# def calculate_shipping(subtotal):
#     return Decimal("0.00")


# @transaction.atomic
# def create_order_from_cart(user):
#     cart = Cart.objects.prefetch_related("items__product").get(user=user)

#     shipping_address = Address.objects.filter(
#         user=user,
#         addy_type=Address.SHIPPING,
#         is_default=True,
#     ).first()

#     if not shipping_address:
#         raise ValueError("Default shipping address is required.")

#     if not cart.items.exists():
#         raise ValueError("Cart is empty.")

#     subtotal = sum(item.line_total for item in cart.items.all())
#     tax = calculate_tax(subtotal)
#     shipping_fee = calculate_shipping(subtotal)
#     total = subtotal + tax + shipping_fee

#     order = Order.objects.create(
#         user=user,
#         shipping_address=shipping_address,
#         subtotal=subtotal,
#         tax=tax,
#         shipping_fee=shipping_fee,
#         total=total,
#     )

#     for item in cart.items.all():
#         OrderItem.objects.create(
#             order=order,
#             product=item.product,
#             product_name=item.product.name,
#             unit_price=item.product.price,
#             quantity=item.quantity,
#             line_total=item.line_total,
#         )

#     cart.items.all().delete()
#     return order