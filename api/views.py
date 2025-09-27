from rest_framework import generics, status, permissions,viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import *
from .serializers import *
from rest_framework.generics import RetrieveAPIView,UpdateAPIView
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.authtoken.models import Token

from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
User = get_user_model()

# Authentication Views


class EmailLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=status.HTTP_400_BAD_REQUEST)

        # authenticate will automatically use USERNAME_FIELD = 'email'
        user = authenticate(request, email=email, password=password)

        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login Successfully..!",
                "token": token.key,
                'username':user.first_name,
               
            }, status=status.HTTP_200_OK)

        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

class TestProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "Authenticated user", "email": request.user.email})


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'user': UserProfileSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'message': 'Account Registration successfully..!'
            }, status=status.HTTP_201_CREATED)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Logout successfully..!'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def refresh_token_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        access_token = token.access_token
        
        return Response({
            'access': str(access_token),
            'message': 'Token refreshed successfully'
        })
    except Exception as e:
        return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def verify_token_view(request):
    try:
        # If we reach here, the token is valid (JWT middleware validated it)
        return Response({
            'valid': True,
            'user': UserProfileSerializer(request.user).data
        })
    except Exception as e:
        pass
    return Response({'valid': False}, status=status.HTTP_401_UNAUTHORIZED)




class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_url = f"http://localhost:5173/reset-password/{uid}/{token}/"  # React URL

            send_mail(
                'Reset your password',
                f'Click the link to reset your password: {reset_url}',
                'suriyathaagam@gmail.com',  # from email
                [user.email],
            )

            return Response({'message': 'Password reset email sent.'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            # Print full traceback to console
            print("Unexpected error:", str(e))
            # traceback.print_exc()
            return Response({'error': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetConfirmView(APIView):
    permission_classes =[permissions.AllowAny]
    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)

            if not default_token_generator.check_token(user, token):
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

            new_password = request.data.get('new_password')
            if not new_password:
                return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()

            return Response({'message': 'Password has been reset successfully'}, status=status.HTTP_200_OK)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class UpdateProfileView(UpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


# Product Views
class StandardResultsSetPagination(PageNumberPagination):
    permission_classes = [permissions.AllowAny]
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProductListView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        try:
            category_id = request.query_params.get('category_id', None)
            products = Product.objects.filter(is_active=True)
            
            if category_id:
                products = products.filter(category_id=category_id)
            
            paginator = StandardResultsSetPagination()
            result_page = paginator.paginate_queryset(products, request)
            serializer = ProductSerializer(result_page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        
        except Exception as e:
            print("💥 Error while fetching products:", str(e))
            return Response({'detail': 'Internal Server Error'}, status=500)


from django.db.models import Q

class ShopFilterListView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print('ShopFilterListView')
        """
        Filters products based on request body parameters:
        {
            "category_id": 1,
            "subcategory": "Mens",
            "color": "Black",
            "size": "M",
            "min_price": 250,
            "max_price": 500
        }
        """
        data = request.data
        # print("data",data)
        category_id = data.get('category')
        subcategory = data.get('subcategory')   # Mens / Womens
        color = data.get('color')               # ex: Black
        size = data.get('size')                 # ex: M
        min_price = data.get('min_price')
        max_price = data.get('max_price')

        products = Product.objects.all()

        # 🔹 Category filter
        if category_id:
            products = products.filter(category_id=category_id)
            # print("category_id",products)
        # 🔹 Gender / subcategory filter
        if subcategory:
            products = products.filter(subcategory=subcategory)
            # print("subcategory",products)
        # 🔹 Color filter
        if color:
            products = products.filter(variants__variant_value__iexact=color)
            # print("color",products)
        # 🔹 Size filter (JSONField → contains lookup)
        if size:
            # Variant match filter (SQLite/MySQL)
            products = products.filter(
                variants__id__in=ProductVariant.objects.extra(
                    where=["JSON_EXTRACT(size, '$') LIKE %s"],
                    params=[f'%\"{size}\"%']
                ).values("id")
            )  
            # print("size",products)
            # # PostgreSQL supports `__contains`
            # products = products.filter(variants__size__contains=[size])


        # 🔹 Price filter
        if min_price and max_price:
            products = products.filter(
               
                Q(variants__price__gte=min_price, variants__price__lte=max_price)
            )
       
        elif min_price:
            products = products.filter(
                 Q(variants__price__gte=min_price)
            )

        elif max_price:
            products = products.filter(
                 Q(variants__price__lte=max_price)
            )

        # 🔹 remove duplicates
        products = products.distinct()
        # print("maibn products",products)
        # Pagination
        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)



class FilterListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category = request.query_params.get('category', None)
        subcategory = request.query_params.get('subcategory', None)

        products = Product.objects.filter(is_active=True)

        if not category:  # covers both None and ""
            products = products.filter(subcategory=subcategory)
           
        else:
            products = products.filter(category__name=category,subcategory=subcategory)
        

        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)




class CategoryListView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        categories = Category.objects.filter(is_active=True)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProductDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer




# Cart Views
class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """View Cart"""
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        """Add to Cart"""
        print(request.data)
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            variant_id = serializer.validated_data.get('variant_id')   # color
            size_variant_id = serializer.validated_data.get('size_variant_id')  # size
            quantity = serializer.validated_data['quantity']

            try:
                product = Product.objects.get(id=product_id, is_active=True)
                cart, _ = Cart.objects.get_or_create(user=request.user)

                # validate variant
                variant = None
                if variant_id:
                    variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)

                # validate size_variant
                size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)

                cart_item_filter = {
                    'cart': cart,
                    'product': product,
                    'variant': variant,
                    'varient_size': size_variant,
                }

                cart_item, created = CartItem.objects.get_or_create(
                    **cart_item_filter,
                    defaults={'quantity': quantity},
                )

                if not created:
                    return Response({'message': 'Item already in cart..!'}, status=status.HTTP_200_OK)

                return Response({'message': 'Item added to cart'}, status=status.HTTP_201_CREATED)

            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            except ProductVariant.DoesNotExist:
                return Response({'error': 'Product variant (color) not found'}, status=status.HTTP_404_NOT_FOUND)
            except SizeVariant.DoesNotExist:
                return Response({'error': 'Size variant not found'}, status=status.HTTP_404_NOT_FOUND)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, item_id):
        """Update Cart Item Quantity"""
        quantity = request.data.get('quantity')

        if item_id is None or quantity is None:
            return Response({'error': 'item_id and quantity are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)

            if int(quantity) <= 0:
                cart_item.delete()
                return Response({'message': 'Item removed from cart'}, status=status.HTTP_200_OK)

            cart_item.quantity = quantity
            cart_item.save()

            cart = cart_item.cart
            total = sum(
                (item.varient_size.get_price if item.varient_size else item.product.get_price) * item.quantity
                for item in cart.items.all()
            )

            return Response({
                'message': 'Cart updated successfully',
                'total': total
            })

        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, item_id):
        """Remove item from cart"""
        if not item_id:
            return Response({'error': 'item_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            cart_item.delete()
            cart, _ = Cart.objects.get_or_create(user=request.user)
            serializer = CartSerializer(cart)

            return Response({'data': serializer.data, 'message': 'Item removed from cart'}, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)



# Wishlist Views
@api_view(['GET'])
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    serializer = WishlistSerializer(wishlist_items, many=True)
    return Response(serializer.data)


class AddToWishlistSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    variant_id = serializers.IntegerField(required=True)
    variant_size = serializers.CharField(required=True)


from django.db import IntegrityError, transaction

class AddToWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToWishlistSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            variant_id = serializer.validated_data['variant_id']
            variant_size = serializer.validated_data['variant_size']

            try:
                product = Product.objects.get(id=product_id, is_active=True)
                try:
                    with transaction.atomic():
                        wishlist_item, created = Wishlist.objects.get_or_create(
                            user=request.user,
                            product=product,
                            variant_id=variant_id,
                            size_variant_id=variant_size
                        )
                except IntegrityError:
                    return Response({'message': 'Item already in wishlist'}, status=status.HTTP_200_OK)

                if created:
                    return Response({'message': 'Item added to wishlist'}, status=status.HTTP_201_CREATED)
                return Response({'message': 'Item already in wishlist'}, status=status.HTTP_200_OK)

            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def remove_from_wishlist(request, product_id):
    try:
        wishlist_item = Wishlist.objects.get(user=request.user, product_id=product_id)
        wishlist_item.delete()
        return Response({'message': 'Item removed from wishlist'})
    except Wishlist.DoesNotExist:
        return Response({'error': 'Wishlist item not found'}, status=status.HTTP_404_NOT_FOUND)

# Order Views
class OrderApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)
    
        
    def post(self, request):
        user = request.user

        try:
            cart = Cart.objects.get(user=user)
            if cart.items.count() == 0:
                return Response({'message': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

            shipping_address = ShippingAddress.objects.filter(user=user, is_default=True).first()
            if not shipping_address:
                return Response({'message': 'Default shipping address not found.'}, status=status.HTTP_400_BAD_REQUEST)

            total_amount = cart.total_price

            order = Order.objects.create(
                user=user,
                total_amount=total_amount,
                shipping_address=shipping_address,
                billing_address=shipping_address.address_line1,
                phone=shipping_address.phone or user.phone,
                email=user.email,
            )

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    size = item.varient_size,
                    quantity=item.quantity,
                    price=int(item.variant.price) * int(item.quantity) ,
                )

            cart.items.all().delete()  # Clear cart after order

            return Response({'message': 'Order created successfully', 'order_id': order.id})

        except Cart.DoesNotExist:
            return Response({'message': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)    

    def put(self, request, order_id):

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        print("Order Update Error:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Order.objects.filter()
    serializer_class = OrderSerializer

class PendingOrderApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        pending_orders = Order.objects.filter(user=request.user, status='pending').order_by('-created_at')
        serializer = OrderSerializer(pending_orders, many=True)

        return Response(serializer.data)


class BuyNowCheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        print("BuyNowCheckoutView",request.data)
        product_id = request.data.get("product_id")
        variant_id = request.data.get("variant_id")      # color
        size_variant_id = request.data.get("size_variant_id")  # ✅ size
        quantity = int(request.data.get("quantity", 1))

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=400)

        # get color variant (optional)
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
            except ProductVariant.DoesNotExist:
                return Response({"detail": "Product variant not found"}, status=400)

        # get size variant (mandatory)
        try:
            size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)
        except SizeVariant.DoesNotExist:
            return Response({"detail": "Size variant not found"}, status=400)

        # effective price
        price = Decimal(size_variant.get_price)

        data = {
            "items": [
                {
                    "product": {
                        "id": product.id,
                        "name": product.name,
                    },
                    "variant": {
                        "id": variant.id if variant else None,
                        "color_name": variant.color_name if variant else None,
                        "hex_color_code": variant.hex_color_code if variant else None,
                        "images": variant.images.first().image.url if variant.images.first() else None,

                    } if variant else None,
                    "varient_size": {
                        "id": size_variant.id,
                        "size": size_variant.size,
                        "sku": size_variant.sku,
                        "price": float(size_variant.price),
                        "discount_price": float(size_variant.discount_price) if size_variant.discount_price else None,
                        "mrp": float(size_variant.mrp) if size_variant.mrp else None,
                        "get_price": float(size_variant.get_price),
                        "stock": size_variant.stock,
                    },
                    "quantity": quantity,
                    "subtotal": float(price * quantity),
                }
            ],
            "total_items": quantity,
            "total_price": float(price * quantity),
        }
        # print("checkout",data)
        return Response(data)




class CartCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"detail": "Cart is empty"}, status=404)

        serializer = CartCheckoutSerializer(cart)
        return Response(serializer.data)

import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@api_view(['POST'])
def create_order(request):
    user = request.user  
    if not user.is_authenticated:
        return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    data = request.data
    print("data",data)
    order_type = data.get('type')  # 'cart' or 'buynow'

    if order_type == 'cart':
        try:
            cart = Cart.objects.get(user=user)
            if not cart.items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

            # Calculate total
            total_amount = cart.total_price  # from CartSerializer / property

            # Create Order
            order = Order.objects.create(
                user=user,
                total_amount=total_amount,
                billing_address='',
                phone=user.phone or '',
                email=user.email,
                notes='',
                source=order_type
            )

            # Create OrderItems from CartItems
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variant=cart_item.variant,  # color
                    size_variant=cart_item.varient_size,  # ✅ FK to SizeVariant
                    quantity=cart_item.quantity,
                    price=cart_item.varient_size.get_price if cart_item.varient_size else cart_item.product.get_price
                )

            # Optional: clear cart after payment success

        except Cart.DoesNotExist:
            return Response({"error": "No cart found"}, status=status.HTTP_400_BAD_REQUEST)

    elif order_type == 'buynow':
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')          # color
        size_variant_id = data.get('size_variant_id')  # ✅ size
        quantity = int(data.get('quantity', 1))

        if not (product_id and variant_id and size_variant_id):
      
            return Response({"error": "Missing product/variant/size"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, is_active=True)
            variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
            size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)

            price = size_variant.get_price
            total_amount = price * quantity

            # Create Order
            order = Order.objects.create(
                user=user,
                total_amount=total_amount,
                billing_address='',
                phone=user.phone or '',
                email=user.email,
                notes='',
                source=order_type
            )

            # Create single OrderItem
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,           # color
                size_variant=size_variant, # ✅ size
                quantity=quantity,
                price=price
            )

        except (Product.DoesNotExist, ProductVariant.DoesNotExist, SizeVariant.DoesNotExist):
            print("error Invalid product/var")
            return Response({"error": "Invalid product/variant/size"}, status=status.HTTP_400_BAD_REQUEST)

    else:
        print()
        return Response({"error": "Invalid type"}, status=status.HTTP_400_BAD_REQUEST)

    # Razorpay Order creation
    try:
        payment_order = client.order.create({
            "amount": int(order.total_amount * 100),  # in paise
            "currency": "INR",
            "payment_capture": "1",
            "notes": {"order_id": order.order_number}
        })

        Payment.objects.create(
            order=order,
            payment_method='Razorpay',
            amount=order.total_amount,
            transaction_id=payment_order['id'],
            gateway_response=payment_order
        )

        return Response({
            "id": payment_order['id'],
            "amount": payment_order['amount'],
            "currency": payment_order['currency'],
            "order_id": order.order_number
        })

    except razorpay.errors.BadRequestError as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


import json
import hmac
import hashlib
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db import transaction

from .models import OrderTracking, TrackingScan
from api.models import Order  # adjust import path if Order is elsewhere

@csrf_exempt
def delhivery_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    # 1) Verify signature (if you set DELHIVERY_WEBHOOK_SECRET)
    secret = getattr(settings, "DELHIVERY_WEBHOOK_SECRET", None)
    if secret:
        # Delhivery might send signature header name differently; try common headers
        signature = request.headers.get("X-DELHIVERY-SIGNATURE") or request.headers.get("X-SIGNATURE") or request.headers.get("X-Hub-Signature")
        if not signature:
            return HttpResponse(status=403)
        computed = hmac.new(secret.encode(), msg=request.body, digestmod=hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, signature):
            return HttpResponse(status=403)

    # 2) Parse JSON body
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    # 3) Extract AWB / event id / shipment info (try a few common shapes)
    awb = payload.get("waybill") or payload.get("awb") or payload.get("waybill_number")
    if not awb:
        # nested style: {"ShipmentData":[{"Shipment":{...}}]}
        try:
            awb = payload.get("ShipmentData", [{}])[0].get("Shipment", {}).get("Waybill")
        except Exception:
            awb = None

    if not awb:
        return HttpResponseBadRequest("AWB not found in payload")

    event_id = payload.get("event_id") or payload.get("id") or payload.get("ShipmentData", [{}])[0].get("EventID")

    # 4) Load tracking row
    try:
        tracking = OrderTracking.objects.get(awb_number=awb)
    except OrderTracking.DoesNotExist:
        # optionally create it or log and return 200 so Delhivery won't retry too aggressively
        return JsonResponse({"status": "tracking_not_found"}, status=200)

    # 5) Idempotency: ignore duplicate event
    if event_id and tracking.last_event_id == event_id:
        return JsonResponse({"status": "duplicate_event"}, status=200)

    # 6) Extract status and scans (generic)
    status = None
    scans_list = []
    if "ShipmentData" in payload:
        shipment = payload["ShipmentData"][0].get("Shipment", {})
        status = shipment.get("Status")
        raw_scans = shipment.get("Scans", [])
        for s in raw_scans:
            scan = s.get("Scan") if isinstance(s, dict) else s
            scans_list.append({
                "status": scan.get("Status"),
                "location": scan.get("Location"),
                "time": scan.get("Time") or scan.get("scan_time")
            })
    else:
        status = payload.get("status") or payload.get("current_status")
        raw_scans = payload.get("scans") or []
        for scan in raw_scans:
            scans_list.append({
                "status": scan.get("status") or scan.get("Status"),
                "location": scan.get("location") or scan.get("Location"),
                "time": scan.get("time") or scan.get("Time")
            })

    # 7) Persist changes inside transaction
    with transaction.atomic():
        tracking.raw_data = payload
        if status:
            tracking.current_status = status
        if event_id:
            tracking.last_event_id = event_id
        tracking.save()

        # Create scans if new (simple de-dup by scan_time + status)
        existing = set(tracking.scans.values_list("scan_time", "status"))
        for s in scans_list:
            scan_time = None
            try:
                scan_time = parse_datetime(s.get("time")) if s.get("time") else None
                if scan_time and timezone.is_naive(scan_time):
                    scan_time = timezone.make_aware(scan_time)
            except Exception:
                scan_time = None

            key = (scan_time, s.get("status"))
            if key in existing:
                continue

            TrackingScan.objects.create(
                tracking=tracking,
                status=s.get("status") or "unknown",
                location=s.get("location"),
                scan_time=scan_time or timezone.now(),
            )

        # 8) Update Order.status mapping (tweak mapping to your terms)
        order = tracking.order
        status_lower = (tracking.current_status or "").lower()
        if "deliv" in status_lower:  # delivered/delivery
            order.status = "Delivered"
        elif "out for delivery" in status_lower or "out_for_delivery" in status_lower:
            order.status = "Shipped"
        elif "transit" in status_lower or "in transit" in status_lower:
            order.status = "Shipped"
        elif "cancel" in status_lower or "returned" in status_lower:
            order.status = "Cancelled"
        order.save()

        # optional: notify user (email/push) if status changed to important states

    return JsonResponse({"status": "ok"}, status=200)



@api_view(['POST'])
def verify_payment(request):
    data = request.data  # Razorpay response: razorpay_order_id, razorpay_payment_id, razorpay_signature
    user = request.user
    
    try:
        # Verify signature (important for security)
        client.utility.verify_payment_signature(data)
        
        # Get your Order from notes or transaction_id
        payment = Payment.objects.get(transaction_id=data['razorpay_order_id'])
        order = payment.order
        
        if order.user != user:
            return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        
        # Update Payment and Order
        payment.status = 'Completed'
        payment.gateway_response = data
        payment.save()
        
        order.status = 'Confirmed'
        order.shipping_address_id = data.get('shipping_address_id')  # Send from frontend if needed
        order.save()
        
        # Clear cart only for cart orders
        if order.source == 'cart' and Cart.objects.filter(user=user).exists():
            Cart.objects.get(user=user).items.all().delete()  # Or delete the whole cart if preferred
        
        return Response({"success": "Payment verified and order confirmed"})
    
    except razorpay.errors.SignatureVerificationError:
        return Response({"error": "Signature verification failed"}, status=status.HTTP_400_BAD_REQUEST)
    except Payment.DoesNotExist:
        return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)



class ShippingAddressListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        addresses = ShippingAddress.objects.filter(user=request.user)
        serializer = ShippingAddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ShippingAddressSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShippingAddressDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return ShippingAddress.objects.get(pk=pk, user=user)
        except ShippingAddress.DoesNotExist:
            return None

    def put(self, request, pk):
        address = self.get_object(pk, request.user)
        if not address:
            return Response({"detail": "Address not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ShippingAddressSerializer(address, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        print("error",serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        address = self.get_object(pk, request.user)
        if not address:
            return Response({"detail": "Address not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ShippingAddressSerializer(address, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        address = self.get_object(pk, request.user)
        if not address:
            return Response({"detail": "Address not found."}, status=status.HTTP_404_NOT_FOUND)
        address.delete()
        return Response({"detail": "Address deleted."}, status=status.HTTP_204_NO_CONTENT)
