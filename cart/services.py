

# from cart.models import Cart, CartItem


# def get_or_create_cart(user):
#     cart, _ = Cart.objects.get_or_create(user=user)
#     return cart


# def add_to_cart(user, product, quantity=1):
#     cart = get_or_create_cart(user)
#     item, created = CartItem.objects.get_or_create(
#         cart=cart,
#         product=product,
#         defaults={"quantity": quantity},
#     )
#     if not created:
#         item.quantity += quantity
#         item.save()
#     return cart


# def update_cart_item(item, quantity):
#     if quantity <= 0:
#         item.delete()
#         return None
#     item.quantity = quantity
#     item.save()
#     return item


# def clear_cart(cart):
#     cart.items.all().delete()