

from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404

from api.models import Address, Product, CartItem, Order, OrderItem
from dj_rest_auth.serializers import UserDetailsSerializer
# from api import services

User = get_user_model()

class CustomUserDetailsSerializer(UserDetailsSerializer):
    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ("is_staff",)

class ProductSerializer(serializers.ModelSerializer):
    category= serializers.CharField( required= False, allow_blank= True)
    image= serializers.ImageField(required= False, allow_null= True)
    image_url= serializers.SerializerMethodField(read_only= True)

    class Meta:
        model= Product
        fields= [
            "id", 
            "sku", 
            "name",
            "image",
            "category", 
            "description", 
            "price", 
            "inventory", 
            "is_active", 
            "created_at",
            "image_url",
        ]
        read_only_fields=("id", "created_at", "image_url")

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image:
            try:
                url= obj.image.url
            except Exception:
                return None
            if request is not None:
                return request.build_absolute_uri(url)
            return url
        return None
    
    def create(self, validated_data):
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

class CartItemSerializer(serializers.ModelSerializer):
    product= ProductSerializer(read_only= True)
    product_id= serializers.PrimaryKeyRelatedField(
        queryset= Product.objects.all(),
        source= "product",
        write_only= True,
    )
    session_key= serializers.CharField(required= False, allow_blank= True, write_only= True)

    class Meta:
        model= CartItem
        fields= ["id", "user", "session_key", "product", "product_id", "quantity", "added_at"]
        read_only_fields= ["id", "added_at", "product", "user"]

    def validate_quantity(self, value):
        if value <1:
            raise serializers.ValidationError("Quantity must be >= 1")
        return value

class CartUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model= CartItem
        fields= ["quantity"]
    
    def validate_quantity(self, value):
        if value <1:
           raise serializers.ValidationError("Quantity must be =/> 1")
        return value
    
class AdressSerializer(serializers.ModelSerializer):
    class Meta:
        model= Address
        fields=["id", "user", "addy_type", "line1", "line2", "city", "state", "country", "postalCode", "formatted_addy", "created_at", "updated_at"]
        read_only_fields= ("user", "created_at", "updated_at")
    
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model= OrderItem
        fields= ["id", "order", "product", "sku", "name", "price", "quantity", "subtotal"]

class OrderSerializer(serializers.ModelSerializer):
    items= OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model= Order
        fields= ["id", "user", "address_line1", "address_line2", "address_city", "address_state",
                  "address_country", "address_postal_code", "address_formatted", "total", "status", "created_at", "items", "updated_at"]

        # fields= [
        #     "id",
        #     "user",
        #     "addy_type",
        #     "line1",
        #     "line2",
        #     "city",
        #     "state",
        #     "country",
        #     "postal_code",
        #     "formatted_addy",
        #     "total",
        #     "status",
        #     "items",
        #     "created_at",
        #     "updated_at",
        # ]
        read_only_fields= ("id", "total", "status", "created_at", "updated_at")

class CheckoutSerializer(serializers.Serializer):
    address_id = serializers.IntegerField(required=False)
    addy_type = serializers.ChoiceField(choices=Address.ADDRESS_TYPES, required=False)
    line1 = serializers.CharField(required=False, allow_blank=True)
    line2 = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)
    formatted_addy = serializers.CharField(required=False, allow_blank=True)
    session_key = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        # Only validate presence of session_key for guest; 
        request= self.context.get("request")
        user= request.user if request and request.user.is_authenticated else None
        if not user and not data.get("session_key"):
            raise serializers.ValidationError("session_key is required for annonymous checkout")
        return data



    




# class UserSignupSerializer(serializers.ModelSerializer):
#     password = serializers.CharField(write_only=True, min_length=6)

#     class Meta:
#         model = User
#         fields = ["id", "username", "email", "phone", "password"]

#     def create(self, validated_data):
#         password = validated_data.pop("password")
#         user = User(**validated_data)
#         user.set_password(password)
#         user.save()
#         return user
    
# class LoginSerializer(serializers.Serializer):
#     username= serializers.CharField()
#     password= serializers.CharField(write_only=True)

#     def validate(self, data):
#         user= authenticate(
#             username= data["username"],
#             password= data["password"]
#         )
#         if not user:
#             raise serializers.ValidationError("Ivalid Credentials")
        
#         data["user"]= user
#         return data


# class AddressSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Address
#         fields = [
#             "id",
#             "addy_entryMode",
#             "addy_type",
#             "line1",
#             "line2",
#             "city",
#             "state",
#             "country",
#             "postalCode",
#             "addytext",
#             "formatted_addy",
#             "provider",
#             "place_id",
#             "lat",
#             "lon",
#             "components",
#             "is_default",
#             "created_at",
#             "updated_at",
#         ]
#         read_only_fields = ["id", "created_at", "updated_at"]

#     def validate(self, attrs):
#         entry_mode = attrs.get(
#             "addy_entryMode",
#             getattr(self.instance, "addy_entryMode", None),
#         )

#         if entry_mode == Address.MANUAL:
#             line1 = attrs.get("line1", getattr(self.instance, "line1", ""))
#             city = attrs.get("city", getattr(self.instance, "city", ""))

#             if not line1 or not city:
#                 raise serializers.ValidationError(
#                     "Manual address requires line1 and city."
#                 )

#         if entry_mode == Address.AUTO:
#             formatted = attrs.get(
#                 "formatted_addy",
#                 getattr(self.instance, "formatted_addy", ""),
#             )
#             place_id = attrs.get(
#                 "place_id",
#                 getattr(self.instance, "place_id", ""),
#             )

#             if not formatted and not place_id:
#                 raise serializers.ValidationError(
#                     "Auto address requires formatted_addy or place_id."
#                 )

#         return attrs

#     @transaction.atomic
#     def create(self, validated_data):
#         user = self.context["request"].user
#         validated_data["user"] = user

#         if validated_data.get("is_default"):
#             Address.objects.filter(
#                 user=user,
#                 addy_type=validated_data["addy_type"],
#                 is_default=True,
#             ).update(is_default=False)

#         return super().create(validated_data)

#     @transaction.atomic
#     def update(self, instance, validated_data):
#         user = self.context["request"].user
#         is_default = validated_data.get("is_default", instance.is_default)
#         addy_type = validated_data.get("addy_type", instance.addy_type)

#         if is_default:
#             Address.objects.filter(
#                 user=user,
#                 addy_type=addy_type,
#                 is_default=True,
#             ).exclude(pk=instance.pk).update(is_default=False)

#         return super().update(instance, validated_data)




































# from django.db import transaction
# from rest_framework import serializers
# from accounts.models import Address


# class AddressSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Address
#         fields = [
#             "id",
#             "addy_entryMode",
#             "addy_type",
#             "line1",
#             "line2",
#             "city",
#             "state",
#             "country",
#             "postalCode",
#             "addytext",
#             "formatted_addy",
#             "provider",
#             "place_id",
#             "lat",
#             "lon",
#             "components",
#             "is_default",
#             "created_at",
#             "updated_at",
#         ]
#         read_only_fields = ["id", "created_at", "updated_at"]

#     def validate(self, attrs):
#         addy_entry_mode = attrs.get(
#             "addy_entryMode",
#             getattr(self.instance, "addy_entryMode", None),
#         )

#         if addy_entry_mode == Address.MANUAL:
#             line1 = attrs.get("line1", getattr(self.instance, "line1", ""))
#             city = attrs.get("city", getattr(self.instance, "city", ""))
#             if not line1 or not city:
#                 raise serializers.ValidationError("Manual address requires line1 and city.")

#         if addy_entry_mode == Address.AUTO:
#             formatted = attrs.get(
#                 "formatted_addy",
#                 getattr(self.instance, "formatted_addy", ""),
#             )
#             place_id = attrs.get(
#                 "place_id",
#                 getattr(self.instance, "place_id", ""),
#             )
#             if not (place_id or formatted):
#                 raise serializers.ValidationError(
#                     "Auto address requires formatted_addy or place_id."
#                 )

#         return attrs

#     @transaction.atomic
#     def create(self, validated_data):
#         user = self.context["request"].user
#         validated_data["user"] = user

#         if validated_data.get("is_default"):
#             Address.objects.filter(
#                 user=user,
#                 addy_type=validated_data["addy_type"],
#                 is_default=True,
#             ).update(is_default=False)

#         return super().create(validated_data)

#     @transaction.atomic
#     def update(self, instance, validated_data):
#         user = self.context["request"].user
#         is_default = validated_data.get("is_default", instance.is_default)
#         addy_type = validated_data.get("addy_type", instance.addy_type)

#         if is_default:
#             Address.objects.filter(
#                 user=user,
#                 addy_type=addy_type,
#                 is_default=True,
#             ).exclude(pk=instance.pk).update(is_default=False)

#         return super().update(instance, validated_data)