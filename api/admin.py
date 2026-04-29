from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import Product, Address, CartItem, Order, OrderItem


# Register your models here.

User= get_user_model()

# @admin.register(User)
# class UserAdmin(DefaultUserAdmin):
#     pass

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display= ("user", "addy_type", "line1", "city", "is_default")
    search_fields= ("user__username", "line1", "city")

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display= ("id", "product", "user", "session_key", "quantity", "added_at")



@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display= ("sku", "name", "price", "inventory", "is_active", "created_at")
    search_fields= ("name", "sku")
    list_filter= ("is_active", "category")

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display= ("id", "user", "total", "status", "created_at")