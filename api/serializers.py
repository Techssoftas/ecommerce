from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
from django.db.models import Q
from django.conf import settings



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'  # this enables email login

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['user_type'] = user.user_type
        token['username'] = user.username
        token['email'] = user.email
        
        return token

    def validate(self, attrs):
        # Override to accept email instead of username
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(request=self.context.get("request"), email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password")
        if not user.is_active:
            raise serializers.ValidationError("User is inactive")

        refresh = self.get_token(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'user_type': user.user_type,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }

    def get_fields(self):
        fields = super().get_fields()
        fields['email'] = serializers.EmailField()
        # del fields['username']
        return fields


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email',  'phone', 
                 'address', 'password', 'password_confirm']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        # Add custom claims
        refresh['user_type'] = user.user_type
        refresh['username'] = user.username
        refresh['email'] = user.email
        
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            data['user'] = user
        else:
            raise serializers.ValidationError('Both username and password are required')
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'phone', 'address', 'user_type', 'profile_image', 'date_joined']
        read_only_fields = ['username', 'date_joined', 'user_type','email']

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'is_active', 'product_count']

    def get_product_count(self, obj):
        return Product.objects.filter(category=obj, is_active=True).count()
    

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['image', 'is_primary', 'alt_text']

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

   


class ProductVariantSerializer(serializers.ModelSerializer):
    get_price = serializers.ReadOnlyField()
    get_savings = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    
   
    class Meta:
        model = ProductVariant
        fields = '__all__'

   


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    category = serializers.StringRelatedField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    primary_image = serializers.SerializerMethodField()
    new_variant  = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category','subcategory', 'price','mrp', 'discount_price', 'brand',
            'variants','description','new_variant','is_bestseller','is_new_arrival',
            'discount_percentage', 'stock', 'images', 'primary_image',
            'availability_status', 'is_active', 'is_featured'
        ]

    def get_primary_image(self, obj):
        primary = obj.images.filter(is_primary=True).first()
        if primary:
            return primary.image.url
        elif obj.images.exists():
            return obj.images.first().image.url
        return None


    def get_new_variant(self, obj):
        three_days_ago = timezone.now() - timedelta(days=7)
        return obj.variants.filter(
            models.Q(created_at__gte=three_days_ago) |
            models.Q(updated_at__gte=three_days_ago)
        ).exists()
    

class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    stock_status = serializers.ReadOnlyField()
    get_savings = serializers.ReadOnlyField()
    get_price_range = serializers.ReadOnlyField()
    has_variants = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'brand', 'short_description', 'price', 'discount_price', 
                 'mrp', 'discount_percentage', 'stock', 'is_active', 'category_name', 
                 'primary_image', 'get_price', 'get_savings', 'stock_status', 
                 'average_rating', 'total_reviews', 'is_featured', 'is_bestseller', 
                 'is_new_arrival', 'is_trending', 'is_deal_of_day', 'is_free_shipping',
                 'delivery_time_min', 'delivery_time_max', 'is_cod_available',
                 'get_price_range', 'has_variants']
    
    def get_primary_image(self, obj):
        primary_image = obj.primary_image
        if primary_image:
            return primary_image.image.url
        return None
    
    def get_has_variants(self, obj):
        return obj.variants.filter(is_active=True).exists()

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True,allow_null=True)
    
    class Meta:
        model = CartItem
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)
    
    # Add total field
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'created_at', 'updated_at', 'user', 'total']

    def get_total(self, obj):
        total = 0
        for item in obj.items.all():
            # Use variant.get_price if variant exists, else product.get_price
            price = item.variant.get_price if item.variant else item.product.get_price
            total += price * item.quantity
        return Decimal(total)
    

class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=True)
    varient_size = serializers.CharField(required=True)
    quantity = serializers.IntegerField(min_value=1, default=1)

class CartCheckoutSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True)
    total_items = serializers.ReadOnlyField()
    total_price = serializers.ReadOnlyField()

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_items', 'total_price']

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = Wishlist
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'



from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

CustomUser = get_user_model()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match."})
        
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})
        
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
    

# Serializer for creating and retrieving ShippingAddress
class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = ['id', 'user', 'address_line1', 'address_line2', 'city', 'state','country', 'postal_code','type_of_address', 'phone', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, data):
        # Ensure only one default address per user
        if data.get('is_default'):
            user = self.context['request'].user
            if ShippingAddress.objects.filter(user=user, is_default=True).exclude(id=self.instance.id if self.instance else None).exists():
                raise serializers.ValidationError({"is_default": "User already has a default address."})
        return data
