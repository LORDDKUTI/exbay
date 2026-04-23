from inspect import signature

from django.http import JsonResponse
import requests
from rest_framework import status, generics,filters, permissions, exceptions, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import permission_classes, api_view, action
from django.shortcuts import get_object_or_404
from django.utils.http import parse_http_date_safe, http_date
from django.http import HttpResponseNotModified
from django.db import transaction
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
import logging

import hmac
import hashlib
import json
from django.http import HttpResponse
from django.conf import settings



from api.models import Address, Product, CartItem, Order, Payment
from api.serializers import ProductSerializer, CartItemSerializer, CartUpdateSerializer, AdressSerializer, OrderSerializer, CheckoutSerializer
from api.services import CartService, create_order_from_cart,initialize_payment, finalize_order_payment





class StandardResusltSetPagination(PageNumberPagination):
    page_size= 12
    page_size_query_param= "page_size"
    max_page_size= 100

class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_staff
        )


##USER
def api_home(request):
    return JsonResponse({
        "message":"Welcome to your store",
        "status": "running"
    })
# @api_view(["GET"])
# def get_singleProduct(request, pk):
#     product= get_object_or_404(Product.objects.select_related("category"), pk=pk)
#     last_modified= get_last_modified_header(product)
#     if last_modified:
#         noneMatch= request.headers.get("If-Modified-Since")
#         if noneMatch:
#             noneMatch_ts= parse_http_date_safe(noneMatch)
#             if noneMatch_ts is not None and int(last_modified.timestamp()) <= noneMatch_ts:
#                 return HttpResponseNotModified
#     serializer= ProductSerializer(product, context= {"request":request})
#     resp= Response(serializer.data)
#     if last_modified:
#         resp["Last_Modified"]= http_date(last_modified.timestamp())
#     resp["Cache-Control"]= "public, max-age=60"
#     return resp

@api_view(["GET"])
def get_Product_Dt(request, pk):
    product= get_object_or_404(Product, pk=pk)
    serializer= ProductSerializer(product, context= {'request':request})
    return Response(serializer.data, status=status.HTTP_200_OK)

class ProductListApiView(generics.ListAPIView):
    queryset= Product.objects.filter(is_active= True).order_by("-created_at")
    serializer_class= ProductSerializer
    permission_classes= [AllowAny]
    pagination_class= StandardResusltSetPagination
    filter_backends= [filters.SearchFilter, filters.OrderingFilter]
    search_fields= ["name", "sku", "description"]
    ordering_fields= ["price", "created_at", "name"]
    ordering= ["-created_at"]

# def productDetail(request, pk):
#     try:
#         product= Product.objects.only("id", "updated_at").get(pk=pk)
#     except Product.DoesNotExist:
#         return None
#     tag= f"{product.id}-{int(product.updated_at.timestamp())}"
#     return 
    
class CartListView(generics.ListAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        request = self.request
        user = request.user if request.user.is_authenticated else None
        session_key = request.query_params.get("session_key")
        return CartService.get_cart_items_for_subject(user=user, session_key=session_key)


class AddToCartView(generics.CreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        """
        Business logic for creating/merging cart items is handled here.
        Expect client to send product_id and quantity; for anonymous include session_key in request.data.
        """
        request = self.request
        user = request.user if request.user.is_authenticated else None
        session_key = request.data.get("session_key")
        product = serializer.validated_data["product"]
        qty = serializer.validated_data.get("quantity", 1)

        if product.inventory < qty:
            raise exceptions.ValidationError({"detail": "Insufficient inventory"})

        with transaction.atomic():
            if user:
                obj, created = CartItem.objects.get_or_create(user=user, product=product, defaults={"quantity": qty})
                if not created:
                    obj.quantity += qty
                    obj.save(update_fields=["quantity"])
                serializer.instance = obj
            else:
                if not session_key:
                    raise exceptions.ValidationError({"detail": "session_key is required for anonymous cart"})
                obj, created = CartItem.objects.get_or_create(session_key=session_key, product=product, defaults={"quantity": qty})
                if not created:
                    obj.quantity += qty
                    obj.save(update_fields=["quantity"])
                serializer.instance = obj


class UpdateCartView(generics.UpdateAPIView):
    serializer_class = CartUpdateSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "pk"

    def get_queryset(self):
        request = self.request
        user = request.user if request.user.is_authenticated else None
        session_key = request.query_params.get("session_key")

        if user:
            return CartItem.objects.select_related("product").filter(user=user)
        if session_key:
            return CartItem.objects.select_related("product").filter(session_key=session_key)
        raise exceptions.ValidationError({"detail": "session_key required"})

    def perform_update(self, serializer):
        qty = serializer.validated_data.get("quantity")
        instance = self.get_object()
        if instance.product.inventory < qty:
            raise exceptions.ValidationError({"detail": "Insufficient inventory."})
        serializer.save()

class DeleteCartView(generics.DestroyAPIView):
    permission_classes = [permissions.AllowAny]
    lookup_field = "pk"

    def get_queryset(self):
        request = self.request
        user = request.user if request.user.is_authenticated else None
        session_key = request.query_params.get("session_key")

        if user:
            return CartItem.objects.select_related("product").filter(user=user)
        if session_key:
            return CartItem.objects.filter(session_key=session_key)
        raise exceptions.ValidationError({"detail": "session_key required."})
    

@api_view(["POST"])
@permission_classes([AllowAny])
def cart_merge_view(request):
    """
    Merge logged out / anonymous and authenticated cart
    """

    if not request.user or not request.user.is_authenticated:
        return Response({"detail": "Authentication required to merge cart."}, status=status.HTTP_401_UNAUTHORIZED)
    session_key = request.data.get("session_key")
    if not session_key:
        return Response({"detail": "session_key required."}, status=status.HTTP_400_BAD_REQUEST)
    merged = CartService.merge_session_into_user(session_key=session_key, user=request.user)
    return Response({"merged": merged}, status=status.HTTP_200_OK)

#checkout
@api_view(["POST"])
@permission_classes([AllowAny])
def checkout_view(request):
    serializer = CheckoutSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)
    user = request.user if request.user.is_authenticated else None
    session_key = serializer.validated_data.get("session_key")
    address_id = serializer.validated_data.get("address_id")
    address_data = {}
    provider= request.data.get("provider", "paystack")

    if address_id and user:
        addr = get_object_or_404(Address, pk=address_id, user=user)
        address_data = {
            "line1": addr.line1,
            "line2": addr.line2,
            "city": addr.city,
            "state": addr.state,
            "country": addr.country,
            "postal_code": addr.postalCode,
            "formatted_addy": addr.formatted_addy,
        }
    else:
        address_data = {
            "line1": serializer.validated_data.get("line1", ""),
            "line2": serializer.validated_data.get("line2", ""),
            "city": serializer.validated_data.get("city", ""),
            "state": serializer.validated_data.get("state", ""),
            "country": serializer.validated_data.get("country", ""),
            "postal_code": serializer.validated_data.get("postal_code", ""),
            "formatted_addy": serializer.validated_data.get("formatted_addy", ""),
        }

    # create_order_from_cart now raises DRF ValidationError on problems, so let it bubble up
    order = create_order_from_cart(
        user= user,
        session_key= session_key,
        address_data=address_data,
    )
    email= request.data.get("email")
    try:
        payment_url= initialize_payment(order, email, provider=provider)
    except exceptions.ValidationError as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except exceptions.APIException as e:
        return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception:
        logger= logging.getLogger(__name__)
        logger.exception("Unexpected error initializing payment")
        return Response({"detail": "Payment initialization failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        "order": OrderSerializer(order, context={"request": request}).data,
        "payment_url": payment_url
        }, status=status.HTTP_201_CREATED
    )



# def checkout_view(request):
#     serializer = CheckoutSerializer(data=request.data, context={"request": request})
#     serializer.is_valid(raise_exception=True)
#     user = request.user if request.user.is_authenticated else None
#     session_key = serializer.validated_data.get("session_key")
#     address_id = serializer.validated_data.get("address_id")
#     address_data = {}

#     # resolve address if provided
#     if address_id and user:
#         addr = get_object_or_404(Address, pk=address_id, user=user)
#         address_data = {
#             "line1": addr.line1,
#             "line2": addr.line2,
#             "city": addr.city,
#             "state": addr.state,
#             "country": addr.country,
#             "postal_code": addr.postalCode,
#             "formatted_addy": addr.formatted_addy,
#         }
#     else:
#         address_data = {
#             "line1": serializer.validated_data.get("line1", ""),
#             "line2": serializer.validated_data.get("line2", ""),
#             "city": serializer.validated_data.get("city", ""),
#             "state": serializer.validated_data.get("state", ""),
#             "country": serializer.validated_data.get("country", ""),
#             "postal_code": serializer.validated_data.get("postal_code", ""),
#             "formatted_addy": serializer.validated_data.get("formatted_addy", ""),
#         }
#     try:
#         order= create_order_from_cart(
#             user=user, 
#             session_key=session_key, 
#             address_data=address_data
#         )
#     except ValueError as e:
#         detail= e.args[0] if e.args else "Invalid request"
#         raise exceptions.ValidationError(detail)
#         # return Response({"detail":e.args[0]}, status=status.HTTP_400_BAD_REQUEST)
    
#     return Response(
#         OrderSerializer(order, context= { "request":request }).data,
#         status=status.HTTP_201_CREATED
#      )
    
#orders
@permission_classes([IsAuthenticated])
class OrderlistView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff and self.request.query_params.get("all") == "1":
            return Order.objects.all().order_by("-created_at")
        return Order.objects.filter(user=user).order_by("-created_at")

@permission_classes([IsAuthenticated])
class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Order.objects.all()
    lookup_field = "pk"

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if user.is_staff or obj.user == user:
            return obj
        self.permission_denied(self.request)


##ADMIN

@api_view(["POST"])
@permission_classes([AllowAny])
def paystack_webhook(request):
    payload= request.body
    signature= request.headers.get("x-paystack-signature")

    computed= hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        payload,
        hashlib.sha512
    ).hexdigest()
    if computed != signature:
        return HttpResponse(status.HTTP_400_BAD_REQUEST)
    
    try:
        event= json.loads(payload)
    except Exception:
        return Response({"detail": "invalid payload"}, status=status.HTTP_400_BAD_REQUEST)
    # Process events idempotently
    event_name= event.get("event")
    data= event.get("data", {})
    reference= data.get("reference")
    if not reference:
        return Response({"detail": "no reference provided"}, status=status.HTTP_400_BAD_REQUEST)
    #fetch the payment from unique reference
    payment= Payment.objects.filter(reference= reference).select_related("order").first()
    if not payment:
        return Response({"detail": "payment not found"}, status=status.HTTP_400_BAD_REQUEST)
    # Idempotency: if already success, just return 200
    if payment.status== "success":
        return Response({"status": "already processed"}, status=status.HTTP_200_OK)
    if event_name== "charge.success":
        with transaction.atomic():
            #mark success
            payment.status= "success"
            payment.save(update_fields=["status"])
            order= payment.order

            try:
                finalize_order_payment(order)
            except Exception as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            order.status= Order.STATUS_PLACED
            order.payment_reference= reference
            order.save(update_fields=["status", "payment_reference"])
            #clear cart 
            if order.user:
                CartItem.objects.filter(user= order.user).delete()
                if order.session_key:
                    CartItem.objects.filter(session_key= order.session_key).delete()
            return Response({ "status": "success", "order_id": order.id }, status=status.HTTP_200_OK)
    elif event_name== "charge.failed":
         # mark payment failed and release inventory 
        with transaction.atomic():
            payment.status= "failed"
            payment.save(update_fields=["status"])
            order= payment.order
            for item in order.items.select_related("product"):
                p= item.product
                if p:
                    p.inventory= p.inventory + item.quantity
                    p.save(update_fields=["status"])
                return Response({"status": "failed"}, status=status.HTTP_200_OK)
    return Response({"status": "unhandled_event"}, status=status.HTTP_200_OK)




    initialize_payment


    # if event["event"]== "charge.success":
    #     reference= event["data"]["reference"]
    #     payment= Payment.objects.filter(reference=reference).first()
    #     if payment and payment.status != "success":
    #         payment.status= "success"
    #         payment.save()
    #         order= payment.order
            
    #         finalize_order_payment(order)
    #         order.status= Order.STATUS_PLACED
    #         CartItem.objects.filter(user= order.user).delete()
    #         if order.session_key:
    #             CartItem.objects.filter(session_key= order.session_key).delete()
    #         order.payment_reference= reference
    #         order.save()
    #         return Response({ "status": "success", "order_status": payment.order.status, "order_id": payment.order.id })
    # elif event["event"] == "charge.failed":
    #     reference= event["data"]["reference"]
    #     payment= Payment.objects.filter(reference= reference).first()
    #     if payment:
    #         payment.status= "failed"
    #         payment.save()
    # return HttpResponse(status=200)

@api_view(["GET"])
def verify_payment(request):
    reference = request.query_params.get("reference")
    if not reference:
        return Response({"error": "No reference provided"}, status=400)

    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"
    }
    res = requests.get(url, headers=headers)
    data = res.json()
    if data["status"] and data["data"]["status"] == "success":
        payment= Payment.objects.filter(reference=reference).select_related("order").first()
        if not payment:
            return Response({"error": "Payment record not found"}, status=404)
        payment.status= "success"
        payment.order.status= Order.STATUS_PLACED
        CartItem.objects.filter(user= payment.order.user).delete()
        if payment.order.session_key:
            CartItem.objects.filter(session_key= payment.order.session_key).delete()
        payment.save()
        payment.order.save()
        return Response({ "status": "success", "order_status": payment.order.status, "order_id": payment.order.id })

    return Response({ "status": "failed", "details": data, }, status=status.HTTP_400_BAD_REQUEST)



@api_view(["POST"])
def retry_payment(request):
    order_id= request.data.get("order_id")
    order= Order.objects.get(id= order_id)

    #retry if not paid..
    if order.status != Order.STATUS_PLACED:
        return Response({"error": "Order already processed"}, status=status.HTTP_400_BAD_REQUEST)
    email= request.data.get("email")
    provider= request.data.get("provider", "paystack")
    payment_url= initialize_payment(order, email, provider)

    return Response({
        "payment_url": payment_url
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response({
        "id": request.user.id,
        "username": request.user.username,
        "is_staff": request.user.is_staff,
    })

class ManagerProductViewSet(viewsets.ModelViewSet):
    """
    Staff-only product management endpoints.
    Routes:
      - GET  /manager/products/             -> list
      - POST /manager/products/             -> create (multipart/form-data)
      - GET  /manager/products/{pk}/        -> retrieve
      - PATCH/PUT/DELETE /manager/products/{pk}/
    """
    queryset = Product.objects.all().order_by("-created_at")
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsStaff]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        # Any extra owner or metadata logic can go here
        return serializer.save()


class ProductApiCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsStaff]

class ProductAdjustInventoryView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsStaff]
    serializer_class = ProductSerializer  # only using partial update to inventory field
   
    def patch(self, request, *args, **kwargs):
        product = self.get_object()
        qty = request.data.get("inventory")
        if qty is None:
            return Response({"detail": "inventory is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            qty = int(qty)
            if qty < 0:
                raise ValueError()
        except ValueError:
            return Response({"detail": "inventory must be a non-negative integer"}, status=status.HTTP_400_BAD_REQUEST)
        product.inventory = qty
        product.save(update_fields=["inventory"])
        return Response(ProductSerializer(product, context={"request": request}).data)

@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsStaff])
def order_status_update(request, pk):
    order = get_object_or_404(Order, pk=pk)
    status_val = request.data.get("status")
    if status_val not in dict(Order._meta.get_field("status").choices):
        return Response({"detail": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
    order.status = status_val
    order.save(update_fields=["status", "updated_at"])
    return Response(OrderSerializer(order, context={"request": request}).data)


# class ProductApiCreateView(generics.CreateAPIView):
#     queryset= Product.objects.all()
#     serializer_class= ProductSerializer
#     permission_classes= [IsStaff]


@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated, IsStaff])
def product_detail(request, pk):
    """
    Admin-only: update or delete a product.
    """
    product = get_object_or_404(Product.objects.select_related("category"), pk=pk)
    if request.method == "DELETE":
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = ProductSerializer(
        product,
        data=request.data,
        partial=True,
        context={"request": request}
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data, status=status.HTTP_200_OK)


def get_last_modified_header(obj):
    return obj.updated_at if getattr(obj, "updated_at", None) else None





# @api_view(["POST"])
# @permission_classes([AllowAny])
# def usersignup(request):
#     serializer = UserSignupSerializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
#     serializer.save()
#     return Response(
#         {"detail": "User created successfully."},
#           status=status.HTTP_201_CREATED,
#         )
    
# @api_view(["POST"])
# @permission_classes([AllowAny])
# def loginuser(request):
#     serializer= LoginSerializer(data= request.data)
#     serializer.is_valid(raise_exception=True)

#     user= serializer.validated_data["user"]
#     refresh= RefreshToken.for_user(user)

#     return Response({
#         "access": str(refresh.access_token),
#         "refresh": str(refresh),
#         "user": {
#             "id":user.id,
#             "username": user.username,
#             "email": user.email,
#         }
#     })
