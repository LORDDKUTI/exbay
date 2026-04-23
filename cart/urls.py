


from django.urls import path
from .views import cart_home

urlpatterns = [
    path("", cart_home, name="cart-home"),
]
























# from django.urls import path
# from cart.views import MyCartView, AddToCartView, UpdateCartItemView

# urlpatterns = [
#     path("", MyCartView.as_view(), name="my-cart"),
#     path("add/", AddToCartView.as_view(), name="add-to-cart"),
#     path("items/<int:pk>/", UpdateCartItemView.as_view(), name="update-cart-item"),
# ]