from django.urls import path, include
from api.views import api_home, ProductListApiView, ProductApiCreateView, ManagerProductViewSet
from .views import get_Product_Dt, product_detail, paystack_webhook
from api import views


manager_list= ManagerProductViewSet.as_view({
    "get": "list",
    "post": "create"
})
manager_detail= ManagerProductViewSet.as_view({
    "get": "retrieve",
    "patch": "partial_update",
    "put": "update",
    "delete": "destroy"
})

urlpatterns = [
    path("home/", api_home, name="api-home"),
    path('auth/', include('dj_rest_auth.urls')),              # login/logout
    path("auth/user/", views.current_user),

    path('auth/registration/', include('dj_rest_auth.registration.urls')),  # signup

    # path("auth/", include("allauth.urls")),  
    
    path("orders/<int:pk>/status/", views.order_status_update, name="orders-status-update"),
    path("products/<int:pk>/adjust/", views.ProductAdjustInventoryView.as_view(), name="product-adjust"),

    #cart
    path("cart/", views.CartListView.as_view(), name="cart-list"),
    path("cart/add/", views.AddToCartView.as_view(), name="add-cart"),
    path("cart/<int:pk>/", views.UpdateCartView.as_view(), name="update-cart"),
    path("cart/<int:pk>/delete/", views.DeleteCartView.as_view(), name="delete-cart"),
    path("cart/merge/", views.cart_merge_view, name="merge-cart"),

    #checkout
    path("checkout/", views.checkout_view, name="checkout"),
    path("webhooks/paystack/", paystack_webhook),
    path("payments/verify/", views.verify_payment, name="verify-payment"),

    #orders
    path("orders/", views.OrderlistView.as_view(), name="orders-list"),
    path("orders/<int:pk>/", views.OrderDetailView.as_view(), name="orders-detail"),


    path("products/", ProductListApiView.as_view(), name="products-list"),
    path("product/add/", ProductApiCreateView.as_view(), name="product-add"),
    path("products/<int:pk>/", get_Product_Dt, name="product-detail"),
    path("products/<int:pk>/manage/", product_detail, name="product-manage"  ),

    #manager
    path("manager/products/", manager_list, name="manager-products-list"),
    path("manager/products/<int:pk>/", manager_detail, name="manager-products-detail"),
]

