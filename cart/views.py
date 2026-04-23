

# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.views import APIView

# from cart.models import CartItem
# from cart.serializers import CartSerializer
# from cart.services import get_or_create_cart, add_to_cart, update_cart_item
# from store.models import Product


from django.http import JsonResponse


def cart_home(request):
    return JsonResponse({"message": "cart app is working"})



# class MyCartView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         cart = get_or_create_cart(request.user)
#         return Response(CartSerializer(cart).data)


# class AddToCartView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         product_id = request.data.get("product_id")
#         quantity = int(request.data.get("quantity", 1))

#         product = Product.objects.filter(pk=product_id).first()
#         if not product:
#             return Response({"detail": "Product not found."}, status=status.HTTP_404_NOT_FOUND)

#         cart = add_to_cart(request.user, product, quantity)
#         return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


# class UpdateCartItemView(APIView):
#     permission_classes = [IsAuthenticated]

#     def patch(self, request, pk):
#         item = CartItem.objects.filter(pk=pk, cart__user=request.user).first()
#         if not item:
#             return Response({"detail": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND)

#         quantity = int(request.data.get("quantity", 1))
#         update_cart_item(item, quantity)

#         cart = get_or_create_cart(request.user)
#         return Response(CartSerializer(cart).data)