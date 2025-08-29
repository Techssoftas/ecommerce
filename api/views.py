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
    
class FilterListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category = request.query_params.get('category', None)
        subcategory = request.query_params.get('subcategory', None)

        products = Product.objects.filter(is_active=True)
        print(category,subcategory)
        if category:
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
            return Response({'message': 'Item removed from cart'}, status=status.HTTP_200_OK)
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


class SingleProductPurchaseAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        product_id = request.data.get("product_id")
        variant_id = request.data.get("variant_id")  # optional
        size = request.data.get("size")  # optional
        quantity = int(request.data.get("quantity", 1))

        if not product_id:
            return Response({"message": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Get product
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"message": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get variant if provided
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
            except ProductVariant.DoesNotExist:
                return Response({"message": "Variant not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get default shipping address
        shipping_address = ShippingAddress.objects.filter(user=user, is_default=True).first()
        if not shipping_address:
            return Response({'message': 'Default shipping address not found.'}, status=status.HTTP_400_BAD_REQUEST)

        # Calculate price
        if variant:
            price = variant.get_price
        else:
            price = product.get_price

        total_amount = price * quantity

        # Create order
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            shipping_address=shipping_address,
            billing_address=shipping_address.address_line1,
            phone=shipping_address.phone or user.phone,
            email=user.email,
        )

        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            variant=variant,
            size=size,
            quantity=quantity,
            price=price,
        )

        return Response({
            "message": "Order placed successfully",
            "order_id": order.id,
            "order_number": order.order_number,
            "total_amount": total_amount
        }, status=status.HTTP_201_CREATED)


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
