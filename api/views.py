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
                "message": "Authenticated Successfully..!",
                "token": token.key,
                'username':user.username,
               
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
        category_id = request.query_params.get('category_id', None)
        products = Product.objects.filter(is_active=True)
        
        if category_id:
            products = products.filter(category_id=category_id)
        
        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

from django.db.models import Q

class ShopFilterListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
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

        category_id = data.get('category_id')
        subcategory = data.get('subcategory')   # Mens / Womens
        color = data.get('color')               # ex: Black
        size = data.get('size')                 # ex: M
        min_price = data.get('min_price')
        max_price = data.get('max_price')

        products = Product.objects.all()

        # 🔹 Category filter
        if category_id:
            products = products.filter(category_id=category_id)
            print("category_id",products)
        # 🔹 Gender / subcategory filter
        if subcategory:
            products = products.filter(subcategory=subcategory)
            print("subcategory",products)
        # 🔹 Color filter
        if color:
            products = products.filter(variants__variant_value__iexact=color)
            print("color",products)
        # 🔹 Size filter (JSONField → contains lookup)
        if size:
            # Variant match filter (SQLite/MySQL)
            products = products.filter(
                variants__id__in=ProductVariant.objects.extra(
                    where=["JSON_EXTRACT(size, '$') LIKE %s"],
                    params=[f'%\"{size}\"%']
                ).values("id")
            )  

            # # PostgreSQL supports `__contains`
            # products = products.filter(variants__size__contains=[size])


        # 🔹 Price filter
        if min_price and max_price:
            products = products.filter(
               
                Q(variants__price__gte=min_price, variants__price__lte=max_price)
            )
            print("min_price and",products)
        elif min_price:
            products = products.filter(
                 Q(variants__price__gte=min_price)
            )
            print("min_price",products)
        elif max_price:
            products = products.filter(
                 Q(variants__price__lte=max_price)
            )
            print("max_price",products)
        # 🔹 remove duplicates
        products = products.distinct()

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
    permission_classes =[permissions.IsAuthenticated]
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
            variant_id = serializer.validated_data.get('variant_id')
            varient_size = serializer.validated_data.get('varient_size')  
            quantity = serializer.validated_data['quantity']

            try:
                product = Product.objects.get(id=product_id, is_active=True)
                cart, _ = Cart.objects.get_or_create(user=request.user)

                cart_item_filter = {'cart': cart, 'product': product}
                if variant_id:
                    variant = ProductVariant.objects.get(id=variant_id, is_active=True)
                    cart_item_filter['variant'] = variant

                cart_item, created = CartItem.objects.get_or_create(
                    **cart_item_filter,
                    defaults={'quantity': quantity},
                    varient_size=varient_size  # Set the size for clothing variants
                )

                if not created:
                    return Response({'message': 'Item already in cart..!'}, status=status.HTTP_200_OK)

                return Response({'message': 'Item added to cart'}, status=status.HTTP_201_CREATED)

            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            except ProductVariant.DoesNotExist:
                return Response({'error': 'Product variant not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request,item_id):
        """Update Cart Item Quantity"""
        item_id = item_id
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
                (item.variant.get_price if item.variant else item.product.get_price) * item.quantity
                for item in cart.items.all()
            )

            return Response({
                'message': 'Cart updated successfully',
                'total': total
            })

        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request,item_id):
        """Remove item from cart"""
        item_id = item_id

        if not item_id:
            return Response({'error': 'item_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            cart_item.delete()
            cart, _ = Cart.objects.get_or_create(user=request.user)
            serializer = CartSerializer(cart)
            
            return Response({'data':serializer.data,'message': 'Item removed from cart'}, status=status.HTTP_200_OK)
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
                            varient_size=variant_size
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
        print(serializer.data)
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
        print(request.data)
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
        print(serializer.data)
        return Response(serializer.data)


class BuyNowCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")
        variant_id = request.data.get("variant_id")
        quantity = int(request.data.get("quantity", 1))

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=404)

        variant = None
        if variant_id:
            variant = ProductVariant.objects.filter(id=variant_id, product=product).first()

        # Price
        price = Decimal(product.get_price)
        if variant:
            price = Decimal(variant.get_price)

     
        data = {
            "items": [
                {
                    "product": {
                        "id": product.id,
                        "name": product.name,
                        
                    },
                    "variant": {
                        "id": variant.id,
                        "size": variant.size,
                        "color": variant.variant_value,
                        "price": float(variant.get_price),
                        "variant_image": variant.variant_image.url if variant.variant_image else None
                    } if variant else None,
                    "quantity": quantity,
                    "subtotal": float(price * quantity),
                }
            ],
            "total_items": quantity,
            "total_price": float(price * quantity),
        }
     
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
    user = request.user  # Assuming authentication middleware sets request.user
    if not user.is_authenticated:
        return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
    
    data = request.data
    type = data.get('type')  # 'cart' or 'buynow' from frontend
    
    if type == 'cart':
        # Get user's cart
        try:
            cart = Cart.objects.get(user=user)
            if not cart.items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate total
            total_amount = cart.total_price  # Uses your @property
            
            # Create Order
            order = Order.objects.create(
                user=user,
                total_amount=total_amount,
                billing_address='',  # Fill if needed
                phone=user.phone or '',  # From user profile?
                email=user.email,
                notes='',
                source=type  # 'cart' or 'buynow'
            )
            
            # Create OrderItems from CartItems
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variant=cart_item.variant,
                    size=cart_item.varient_size or '',
                    quantity=cart_item.quantity,
                    price=cart_item.variant.price if cart_item.variant else cart_item.product.get_price
                )
            
            # (Optional: Don't clear cart yet, do it after payment success)
        
        except Cart.DoesNotExist:
            return Response({"error": "No cart found"}, status=status.HTTP_400_BAD_REQUEST)
    
    elif type == 'buynow':
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        quantity = data.get('quantity', 1)
        
        if not (product_id and variant_id and quantity):
            return Response({"error": "Missing product/variant/quantity"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
            variant = ProductVariant.objects.get(id=variant_id)
            
            price = variant.price
            total_amount = price * int(quantity)
            
            # Create Order
            order = Order.objects.create(
                user=user,
                total_amount=total_amount,
                billing_address='',  # Fill if needed
                phone=user.phone or '',
                email=user.email,
                notes='',
                source=type  # 'cart' or 'buynow'
            )
            
            # Create single OrderItem
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                size='',  # If applicable
                quantity=quantity,
                price=price
            )
        
        except (Product.DoesNotExist, ProductVariant.DoesNotExist):
            return Response({"error": "Invalid product/variant"}, status=status.HTTP_400_BAD_REQUEST)
    
    else:
        return Response({"error": "Invalid type"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Now create Razorpay order
    try:
        print("amount", int(order.total_amount * 100))
        payment_order = client.order.create({
           
            "amount": int(order.total_amount * 100),  # In paise
            "currency": "INR",
            "payment_capture": "1",  # Auto capture
            "notes": {"order_id": order.order_number}  # Link to your Order
        })
        
        # Create Payment record (pending)
        Payment.objects.create(
            order=order,
            payment_method='razorpay',  # Or from data
            amount=order.total_amount,
            transaction_id=payment_order['id'],
            gateway_response=payment_order
        )
        
        return Response({
            "id": payment_order['id'],
            "amount": payment_order['amount'],
            "currency": payment_order['currency'],
            "order_id": order.order_number  # Your Django order.order_number, for later use
        })
    
    except razorpay.errors.BadRequestError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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
        payment.status = 'completed'
        payment.gateway_response = data
        payment.save()
        
        order.status = 'confirmed'
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
