# from django.shortcuts import render

# # Create your views here.

# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.views import APIView

# from orders.serializers import OrderSerializer
# from orders.services import create_order_from_cart
# from orders.models import Order


# class CheckoutView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         try:
#             order = create_order_from_cart(request.user)
#         except ValueError as e:
#             return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#         return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


from django.http import JsonResponse


def orders_home(request):
    return JsonResponse({"message": "orders app is working"})

# class MyOrdersView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         orders = Order.objects.filter(user=request.user).prefetch_related("items")
#         return Response(OrderSerializer(orders, many=True).data)