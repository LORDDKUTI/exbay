


from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class User(AbstractUser):
    phone = models.CharField(max_length=13, blank=True)

    def __str__(self):
        return f"{self.username} - {self.email}"


class Address(models.Model):
    SHIPPING = "shipping"
    BILLING = "billing"
    ADDRESS_TYPES = [
        (SHIPPING, "Shipping"),
        (BILLING, "Billing"),
    ]

    MANUAL = "manual"
    AUTO = "auto"
    ENTRY_MODES = [
        (MANUAL, "Manual"),
        (AUTO, "Auto"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    addy_entryMode = models.CharField(
        max_length=20,
        choices=ENTRY_MODES,
        default=MANUAL,
    )
    addy_type = models.CharField(
        max_length=20,
        choices=ADDRESS_TYPES,
    )

    line1 = models.CharField(max_length=255, blank=True)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=10, blank=True)
    postalCode = models.CharField(max_length=20, blank=True)
    addytext = models.TextField(blank=True)

    formatted_addy = models.CharField(max_length=255, blank=True)
    provider = models.CharField(max_length=50, blank=True)
    place_id = models.CharField(max_length=255, blank=True)
    lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    lon = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    components = models.JSONField(default=dict, blank=True)

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-updated_at"]

    def __str__(self):
        return f"{self.user.username} - {self.addy_type} - {self.line1 or self.formatted_addy}"

class Product(models.Model):
    sku= models.CharField(max_length=64, unique=True)
    name= models.CharField(max_length=200)
    image= models.ImageField(upload_to="products", null=True, blank=True)
    category= models.CharField(max_length=50, blank=True)
    description= models.TextField(blank=True)
    price= models.DecimalField(max_digits=10, decimal_places=2)
    inventory= models.PositiveBigIntegerField(default=0)
    is_active= models.BooleanField(default=True)
    created_at= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"


class CartItem(models.Model):
    user= models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="cart_items",)
    session_key= models.CharField(max_length=40, null=True, blank=True, db_index=True)
    product= models.ForeignKey("api.Product", on_delete=models.CASCADE, related_name="cart_items")
    quantity= models.PositiveBigIntegerField(default=1)
    added_at= models.DateTimeField(auto_now_add=True)

    class Meta:
       constraints= [
           models.UniqueConstraint(fields=["user", "product"], name="unique_user_product"),
           models.UniqueConstraint(fields=["session_key", "product"], name="unique_session_product"),
       ]
       
    def subtotal(self):
        return self.quantity * self.product.price
    
    def __str__(self):
        owner= self.user.username if self.user else f"session:{self.session_key}"
        return f"{owner} - {self.product.name} x {self.quantity}"
    
    def clean(self):
        #ensure user or session_key prezn
        if not self.user and not self.session_key:
            raise ValidationError("CartItem must have either user or session_key.")
        if self.user and self.session_key:
            self.session_key= None
        return super().clean()
    
    def save(self, *args, **kwargs):
        self.full_clean()
       
        super().save(*args, **kwargs)


class Order(models.Model):

    STATUS_PLACED = "placed"
    STATUS_PROCESSING = "processing"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES= [
        (STATUS_PLACED, "Placed"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled")
    ]

    user= models.ForeignKey(settings.AUTH_USER_MODEL, null=True,  blank=True, on_delete=models.SET_NULL, related_name="orders")
    session_key= models.CharField(max_length=40, null=True, blank=True)
    # Snapshot Addy
    address_line1= models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    address_city = models.CharField(max_length=100, blank=True)
    address_state = models.CharField(max_length=100, blank=True)
    address_country = models.CharField(max_length=10, blank=True)
    address_postal_code = models.CharField(max_length=20, blank=True)
    address_formatted = models.TextField(blank=True)

    total= models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status= models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_PLACED)
    created_at= models.DateTimeField(auto_now_add=True)
    updated_at= models.DateTimeField(auto_now=True)
    payment_reference= models.CharField(max_length=255, blank=True)

    class Meta:
        ordering= ["-created_at"]

    def __str__(self):
        owner= self.user.username if self.user else f"session:{self.session_key}"
        return f"order {self.id} - {owner} - {self.total}"
    
class OrderItem(models.Model):
    order= models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product= models.ForeignKey("api.Product", null=True, blank=True, on_delete=models.SET_NULL)
    sku= models.CharField(max_length=200)
    name= models.CharField(max_length=200)
    price= models.DecimalField(max_digits=12, decimal_places=2)
    quantity= models.PositiveIntegerField()
    subtotal= models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal= self.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} x {self.quantity}"

class Payment(models.Model):
    PROVIDER_CHOICES= [
        ("paystack", "Paystack"),
        ("stripe", "Stripe"),
    ]

    STATUS_CHOICES= [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    order= models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    provider= models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    reference= models.CharField(max_length=255, unique=True)
    amount= models.DecimalField(max_digits=12, decimal_places=2)
    status= models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at= models.DateTimeField(auto_now_add=True)



# from django.db import models
# from django.contrib.auth.models import AbstractUser


# class User(AbstractUser):
#     phone = models.CharField(max_length=13, blank=True)

#     def __str__(self):
#         return f"{self.username}-{self.email}"


# class Address(models.Model):
#     SHIPPING = "shipping"
#     BILLING = "billing"
#     ADDRESS_TYPES = [
#         (SHIPPING, "Shipping"),
#         (BILLING, "Billing"),
#     ]

#     MANUAL = "manual"
#     AUTO = "auto"
#     ENTRY_MODES = [
#         (MANUAL, "Manual"),
#         (AUTO, "Auto"),
#     ]

#     user = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name="addresses",
#     )
#     addy_entryMode = models.CharField(
#         max_length=20,
#         choices=ENTRY_MODES,
#         default=MANUAL,
#     )
#     addy_type = models.CharField(
#         max_length=20,
#         choices=ADDRESS_TYPES,
#     )

#     line1 = models.CharField(max_length=255, blank=True)
#     line2 = models.CharField(max_length=255, blank=True)
#     city = models.CharField(max_length=100, blank=True)
#     state = models.CharField(max_length=100, blank=True)
#     country = models.CharField(max_length=10, blank=True)
#     postalCode = models.CharField(max_length=20, blank=True)
#     addytext = models.TextField(blank=True)

#     formatted_addy = models.CharField(max_length=255, blank=True)
#     provider = models.CharField(max_length=50, blank=True)
#     place_id = models.CharField(max_length=255, blank=True)
#     lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
#     lon = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
#     components = models.JSONField(default=dict, blank=True)

#     is_default = models.BooleanField(default=False)

#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ["-is_default", "-updated_at"]

#     def __str__(self):
#         return f"{self.user.username} - {self.addy_type} - {self.line1 or self.formatted_addy}"