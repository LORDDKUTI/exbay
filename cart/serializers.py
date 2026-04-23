

# from rest_framework import serializers
# from cart.models import Cart, CartItem


# class CartItemSerializer(serializers.ModelSerializer):
#     unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
#     line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

#     class Meta:
#         model = CartItem
#         fields = ["id", "product", "quantity", "unit_price", "line_total"]


# class CartSerializer(serializers.ModelSerializer):
#     items = CartItemSerializer(many=True, read_only=True)
#     subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

#     class Meta:
#         model = Cart
#         fields = ["id", "items", "subtotal", "created_at", "updated_at"]