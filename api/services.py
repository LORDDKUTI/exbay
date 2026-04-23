# api/services.py
from decimal import Decimal
from time import time
from django.db import transaction
from django.shortcuts import get_object_or_404
import requests
from rest_framework import exceptions
import uuid
import logging
from django.conf import settings
from django.utils import timezone
import stripe

from api.models import Product, Address, CartItem, Order, OrderItem, Payment
from django.conf import settings

logger= logging.getLogger(__name__)

class CartService:
    @staticmethod
    def get_cart_items_for_subject(*, user=None, session_key=None):
        if user is not None and getattr(user, "is_authenticated", False):
            return CartItem.objects.filter(user=user).select_related("product")
        if session_key:
            return CartItem.objects.filter(session_key=session_key).select_related("product")

        return CartItem.objects.none()

    @staticmethod
    def merge_session_into_user(session_key: str, user):
        """
        Move/merge cart items belonging to session_key into user's cart.
        """
        if not session_key or not user or not user.is_authenticated:
            return 0
        merged = 0
        with transaction.atomic():
            user_items_qs = CartItem.objects.select_for_update().filter(user=user)
            user_items_map = {ci.product_id: ci for ci in user_items_qs}
            session_items = list(CartItem.objects.select_for_update().filter(session_key=session_key))
            for si in session_items:
                ui = user_items_map.get(si.product_id)
                if ui:
                    ui.quantity = ui.quantity + si.quantity
                    ui.save(update_fields=["quantity"])
                else:
                    si.user = user
                    si.session_key = None
                    si.save(update_fields=["user", "session_key"])
                merged += 1
            return merged


def create_order_from_cart(*, user=None, session_key=None, address_data: dict = None, payment_reference: str = ""):
    """
    Create Order and OrderItems from cart subject (user or session_key).
    Performs inventory checks and deductions inside a transaction using select_for_update.
    Returns created Order.
    Raises rest_framework.exceptions.ValidationError on insufficient inventory or invalid input.
    """

    if user and user.is_authenticated:
        cart_qs = CartItem.objects.select_related("product").filter(user=user)
    elif session_key:
        cart_qs = CartItem.objects.select_related("product").filter(session_key=session_key)
    else:
        raise exceptions.ValidationError("user or session key required to order")

    if not cart_qs.exists():
        raise exceptions.ValidationError("Empty Cart")
    address_data = address_data or {}

    with transaction.atomic():
        # Lock product rows
        product_ids = list({ci.product_id for ci in cart_qs})
        products = Product.objects.select_for_update().filter(id__in=product_ids)
        prod_map = {p.id: p for p in products}
        # product availability
        insufficient = []
        for ci in cart_qs:
            p = prod_map.get(ci.product_id)
            if p is None:
                insufficient.append({"product_id": ci.product_id, "reason": "missing"})
                continue
            if p.inventory < ci.quantity:
                insufficient.append({"sku": p.sku, "available": p.inventory, "requested": ci.quantity})
        if insufficient:
            raise exceptions.ValidationError({"insufficient_inventory": insufficient})

        # Create order
        order = Order.objects.create(
            user=(user if user and user.is_authenticated else None),
            address_line1=address_data.get("line1", ""),
            address_line2=address_data.get("line2", ""),
            address_city=address_data.get("city", ""),
            address_state=address_data.get("state", ""),
            address_country=address_data.get("country", ""),
            address_postal_code=address_data.get("postal_code", ""),
            address_formatted=address_data.get("formatted_addy", ""),
            total=Decimal("0.00"),
            payment_reference=payment_reference or "",
            status= Order.STATUS_PROCESSING,  # processing/reserved until payment confirmation
        )
        total = Decimal("0.00")
        # create and deduct from inventory
        for ci in cart_qs:
            p = prod_map[ci.product_id]
            # deduct right away
            p.inventory = p.inventory - ci.quantity
            p.save(update_fields=["inventory"])
            oi = OrderItem.objects.create(
                order=order,
                product=p,
                sku=p.sku,
                name=p.name,
                price=p.price,
                quantity=ci.quantity,
                subtotal=(p.price * ci.quantity),
            )
            total += oi.subtotal
        order.total = total
        order.save(update_fields=["total", "status"])
       # Note:keep cartuntil payment succeeds 

        return order

def initialize_paystack_payment(order, email):
    url = "https://api.paystack.co/transaction/initialize"
    reference= f"webstore-{order.id}-{uuid.uuid4().hex[:8]}"
    # reference= str(order.id)
    ##ensure Payment record exist with rec
    Payment.objects.create(
        order=order,
        reference= reference,
        amount= order.total,
        status= "pending",
        provider= "paystack",
    )   
    if not getattr(settings, "PAYSTACK_SECRET_KEY", None):
        raise exceptions.APIException("PAYSTACK_SECRET_KEY is not configured in server settings.") 

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "email": email,
        "amount": int(order.total * 100),  # Paystack uses kobo
        "reference": reference,
        "callback_url": f"{settings.FRONTEND_URL}/payment/callback",
    }
    logger.info("Paystack init header present: %s", bool(headers.get("Authorization")))   
    try:
        response= requests.post(url, json= data, headers=headers, timeout=10)
    except requests.RequestException as e:
        logger.exception("Paystack initialize network error")
        raise exceptions.APIException("Network error initializing Paystack payment") from e
    try:
        res_data= response.json()
    except ValueError:
        logger.exception("Paystack returned non-json response")
        raise exceptions.APIException("Invalid response from payment provider.")
    
    if not res_data.get("status"):
        msg = res_data.get("message") or res_data
        raise exceptions.ValidationError({"payment_init_error": str(msg)})
    auth_url= res_data.get("data", {}).get("authorization_url")
    if not auth_url:
        raise exceptions.ValidationError({"payment_init_error": "authorization_url missing"})
        
    return auth_url




stripe.api_key = settings.STRIPE_SECRET_KEY
def initialize_stripe_payment(order, email):
    session= stripe.checkout.Session.create(
        payment_method_types= ["card"],
        line_items= [{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": "Order Payment",
                },
                "unit_amount": int(order.total * 100),
            },
            "quantity": 1,
        }],
        mode= "payment",
        success_url= f"http://localhost:3000/order-success/{order.id}",
        cancel_url= "https://example.com/cancel",
    )
    return session

def initialize_payment(order, email, provider):
    if settings.DEBUG and provider== "mock":
        return f"{settings.FRONTEND_URL}/payment/mock?ref=local-{order.id}"
    if provider== "paystack":
        return initialize_paystack_payment(order, email)
    elif provider== "stripe":
        res= initialize_stripe_payment(order, email)
        return getattr(res, "url", None) or res
    else:
        raise exceptions.ValidationError({"provider": "Unsupported payment provider"})
        # res= initialize_paystack_payment(order, email)
        # authorization_url= res.get("data", {}).get("authorization_url")
        # if not authorization_url:
        #     raise exceptions.APIException(f"Failed to initialize Paystack payment: {res}")
        # return authorization_url


def finalize_order_payment(order):
    with transaction.atomic():
        """
        With reservation flow, inventory was already deducted at order creation.
        This finalization only ensures all items still exist and finalizes the order.
        If you used the older flow where inventory was deducted at finalize, you'd keep that logic here.
        """
        with transaction.atomic():
            for item in order.items.select_related("product"):
                product= item.product
                if product is None:
                    raise exceptions.ValidationError({"missing_product": {"sku": item.sku}})
                if product.inventory < 0:
                    raise exceptions.ValidationError({"insufficient_inventory": {"sku": product.sku}})
                # clear cart after successful payment ..in webhook
                if order.user:
                    CartItem.objects.filter(user= order.user).delete()
                    if order.session_key:
                        CartItem.objects.filter(session_key= order.session_key).delete()
                

        # items= order.items.select_related("product")

        # for item in items:
        #     product= item.product
        #     if product.inventory < item.quantity:
        #         raise exceptions.ValidationError({"insufficient_inventory": {"sku": product.sku, "available": product.inventory, "requested": item.quantity}})
        #     product.inventory -= item.quantity
        #     product.save(update_fields=["inventory"])

    #clear cart AFTER successful payment
    if order.user:
        CartItem.objects.filter(
            user= order.user if order.user else None
        ).delete()










# from decimal import Decimal
# from django.db import transaction
# from django.shortcuts import get_object_or_404

# from api.models import Product, Address, CartItem, Order, OrderItem


# class CartService:
#     @staticmethod
#     def get_cart_items_for_subject(*, user=None, session_key=None):
#         if user is not None and getattr(user, "is_authenticated", False):
#             return CartItem.objects.filter(user=user).select_related("product")
#         if session_key:
#             return CartItem.objects.filter(session_key=session_key).select_related("product")
        
#         return CartItem.objects.none()
    
#     @staticmethod
#     def merge_session_into_user(session_key: str, user):
#         """
#         Move/merge cart items belonging to session_key into user's cart.
#         """
#         if not session_key or not user or not user.is_authenticated:
#             return 0
#         # session_items= CartItem.objects.filter(session_key=session_key)
#         merged= 0
#         with transaction.atomic():
#             user_items_qs= CartItem.objects.select_for_update().filter(user=user)
#             user_items_map= {ci.product_id: ci for ci in user_items_qs}
#             session_items= list(CartItem.objects.select_for_update().filter(session_key=session_key))       
#             for si in session_items:
#                 ui= user_items_map.get(si.product_id)
#                 if ui:
#                     ui.quantity= ui.quantity + si.quantity
#                     ui.save(update_fields= ["quantity"])
#                 else:
#                     si.user= user
#                     si.session_key= None
#                     si.save(update_fields= ["user", "session_key"])
#                 merged += 1
#             return merged
             
    
# def create_order_from_cart(*, user=None, session_key=None, address_data: dict = None, payment_reference: str = ""):
#     """
#     Create Order and OrderItems from cart subject (user or session_key).
#     Performs inventory checks and deductions inside a transaction using select_for_update.
#     Returns created Order.
#     Raises ValueError on insufficient inventory or invalid input.
#     """

#     if user and user.is_authenticated:
#         cart_qs= CartItem.objects.select_related("product").filter(user=user)
#     elif session_key:
#         cart_qs= CartItem.objects.select_related("product").filter(session_key=session_key)
#     else:
#         raise ValueError("user or session key required to order")
    
#     if not cart_qs.exists():
#         raise ValueError("Empty Cart")
#     address_data= address_data or {}

#     with transaction.atomic():
#         # Lock product rows
#         product_ids = list({ ci.product_id for ci in cart_qs })
#         products = Product.objects.select_for_update().filter(id__in=product_ids)
#         prod_map = {p.id: p for p in products}
#         # product availability
#         insufficient = []
#         for ci in cart_qs:
#             p = prod_map.get(ci.product_id)
#             if p is None:
#                 insufficient.append({"product_id": ci.product_id, "reason": "missing"})
#                 continue
#             if p.inventory < ci.quantity:
#                 insufficient.append({"sku": p.sku, "available": p.inventory, "requested": ci.quantity})
#         if insufficient:
#             raise ValueError({"insufficient_inventory": insufficient})
        
#         # Create order 
#         order= Order.objects.create(
#             user=(user if user and user.is_authenticated else None),
#             address_line1=address_data.get("line1", ""),
#             address_line2=address_data.get("line2", ""),
#             address_city=address_data.get("city", ""),
#             address_state=address_data.get("state", ""),
#             address_country=address_data.get("country", ""),
#             address_postal_code=address_data.get("postal_code", ""),
#             address_formatted=address_data.get("formatted_addy", ""),
#             total=Decimal("0.00"),
#             payment_reference=payment_reference or "",
#         )
#         total= Decimal("0.00")
#         #create order itms and deduct from inventory
#         for ci in cart_qs:
#             p= prod_map[ci.product_id]
#             #deduct
#             p.inventory= p.inventory - ci.quantity
#             p.save(update_fields=["inventory"])
#             oi= OrderItem.objects.create(
#                 order=order,
#                 product=p,
#                 sku=p.sku,
#                 name=p.name,
#                 price=p.price,
#                 quantity=ci.quantity,
#                 subtotal=(p.price * ci.quantity),
#             )
#             total += oi.subtotal
        
#         order.total= total
#         order.save(update_fields=["total"])

#         #clesr cart
#         cart_qs.delete()

#         return order







