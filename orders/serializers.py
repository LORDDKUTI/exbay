

# from rest_framework import serializers
# from orders.models import Order, OrderItem


# class OrderItemSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = OrderItem
#         fields = [
#             "id",
#             "product",
#             "product_name",
#             "unit_price",
#             "quantity",
#             "line_total",
#         ]


from django.http import JsonResponse


def orders_home(request):
    return JsonResponse({"message": "orders app is working"})


# class OrderSerializer(serializers.ModelSerializer):
#     items = OrderItemSerializer(many=True, read_only=True)

#     class Meta:
#         model = Order
#         fields = [
#             "id",
#             "status",
#             "shipping_address",
#             "billing_address",
#             "subtotal",
#             "tax",
#             "shipping_fee",
#             "total",
#             "created_at",
#             "items",
#         ]