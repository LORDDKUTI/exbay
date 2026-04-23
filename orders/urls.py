

# from django.urls import path
# from orders.views import CheckoutView, MyOrdersView

# urlpatterns = [
#     path("checkout/", CheckoutView.as_view(), name="checkout"),
#     path("", MyOrdersView.as_view(), name="my-orders"),
# ]from django.urls import path
from django.urls import path
from .views import orders_home

urlpatterns = [
    path("", orders_home, name="orders-home"),
]