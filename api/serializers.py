from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import *
from django.db.models import Q
from django.conf import settings
from .utils import is_within_return_window, get_delivered_time
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
CustomUser = get_user_model()
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
    password = serializers.CharField(write_only=True, min_length=5)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'username', 'first_name', 'email',
            'phone', 'address',
            'password', 'password_confirm'
        ]



    def validate_phone(self, value):
        if CustomUser.objects.filter(phone=value).exists():
            raise serializers.ValidationError("PhoneNumber is already registered.")
        return value
    # def validate_email(self, value):
    #     if CustomUser.objects.filter(email=value).exists():
    #         raise serializers.ValidationError("Email is already registered.")
    #     return value
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match.")
        
        username = data.get('username')
        print("First Name:", username)
        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username already exists. Please choose another first name.")


        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')

        # Set username = first_name
        
        user = CustomUser.objects.create_user(**validated_data)
        username = validated_data.get('username')
        user.first_name = username
        user.set_password(password)
        user.save()

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
        read_only_fields = ['username', 'date_joined', 'user_type','phone']

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

   


class ProductVariantImageSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = ProductVariantImage
        fields = '__all__'

class ProductSizeVariantSerializer(serializers.ModelSerializer):
    get_price = serializers.ReadOnlyField()
    get_savings = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()

    class Meta:
        model = SizeVariant
        fields = ['id', 'size', 'sku', 'price', 'discount_price', 'mrp', 'stock',
                  'get_price', 'get_savings', 'discount_percentage', 'is_in_stock']


class ProductVariantSerializer(serializers.ModelSerializer):
    sizes = ProductSizeVariantSerializer(many=True, read_only=True)
    images = ProductVariantImageSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = ['id', 'product', 'color_name', 'hex_color_code', 'is_active',
                  'created_at', 'updated_at', 'sizes', 'images']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    category = serializers.StringRelatedField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_price = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    primary_image = serializers.SerializerMethodField()
    new_variant  = serializers.SerializerMethodField()
    is_new_arrival = serializers.BooleanField()
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category','subcategory', 'price','mrp', 'discount_price', 'brand',
            'variants','description','new_variant','is_bestseller','is_new_arrival','key_features',
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
    

# Dashboard Serializers
class DashboardProductImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    image = serializers.ImageField(required=False)
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary', 'alt_text']

class DashboardSizeVariantSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    class Meta:
        model = SizeVariant
        fields = ['id', 'size', 'sku', 'price', 'discount_price', 'mrp', 'stock']

class DashboardProductVariantImageSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    image = serializers.ImageField(required=False)
    class Meta:
        model = ProductVariantImage
        fields = ['id', 'image', 'is_default']

class DashboardProductVariantSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    sizes = DashboardSizeVariantSerializer(many=True, required=False)
    images = DashboardProductVariantImageSerializer(many=True, required=False)

    class Meta:
        model = ProductVariant
        fields = ['id', 'color_name', 'variant_sku', 'hex_color_code', 'is_active', 'sizes', 'images']

class DashboardProductSerializer(serializers.ModelSerializer):
    images = DashboardProductImageSerializer(many=True, required=False)
    variants = DashboardProductVariantSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = '__all__'

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        variants_data = validated_data.pop('variants', [])
        
        product = Product.objects.create(**validated_data)
        
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)
            
        for variant_data in variants_data:
            sizes_data = variant_data.pop('sizes', [])
            variant_images_data = variant_data.pop('images', [])
            
            variant = ProductVariant.objects.create(product=product, **variant_data)
            
            for size_data in sizes_data:
                SizeVariant.objects.create(variant=variant, **size_data)
                
            for variant_image_data in variant_images_data:
                ProductVariantImage.objects.create(variant=variant, **variant_image_data)
                
        return product

    def update(self, instance, validated_data):
        # Update simple fields
        fields = ['name', 'brand', 'model_name', 'fabric', 'occasion', 'short_description', 
                  'description', 'specifications', 'key_features', 'category', 'subcategory', 
                  'price', 'discount_price', 'discount_percentage', 'mrp', 'stock', 
                  'minimum_order_quantity', 'maximum_order_quantity', 'sku', 'barcode', 'hsn_code',
                  'weight', 'dimensions_length', 'dimensions_width', 'dimensions_height',
                  'condition', 'availability_status', 'meta_title', 'meta_description', 'tags',
                  'is_free_shipping', 'shipping_weight', 'delivery_time_min', 'delivery_time_max',
                  'is_active', 'is_featured', 'is_bestseller', 'is_new_arrival', 'is_trending',
                  'is_deal_of_day', 'is_returnable', 'is_replaceable', 'is_cod_available',
                  'warranty_period', 'warranty_type', 'warranty_description',
                  'return_period', 'replace_period', 'return_policy']
        
        for field in fields:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        instance.save()

        # Update Images
        if 'images' in validated_data:
            images_data = validated_data.pop('images')
            self._update_nested_relation(
                instance, images_data, 'images', ProductImage, 'product'
            )

        # Update Variants
        if 'variants' in validated_data:
            variants_data = validated_data.pop('variants')
            self._update_variants(instance, variants_data)

        return instance

    def _update_nested_relation(self, parent, data_list, related_name, ModelClass, parent_field_name):
        existing_items = {item.id: item for item in getattr(parent, related_name).all()}
        kept_ids = []

        for data in data_list:
            item_id = data.get('id')
            if item_id and item_id in existing_items:
                # Update
                item = existing_items[item_id]
                for key, value in data.items():
                    setattr(item, key, value)
                item.save()
                kept_ids.append(item_id)
            else:
                # Create
                # Remove id from data if None or not present, though pop('id', None) inside loop is safer
                if 'id' in data:
                    del data['id'] 
                data[parent_field_name] = parent
                new_item = ModelClass.objects.create(**data)
                kept_ids.append(new_item.id)
        
        # Delete removed items (Optional - depending on requirements, usually safe to delete if sending full list)
        # For this request, I'll assume full sync.
        for item_id, item in existing_items.items():
            if item_id not in kept_ids:
                item.delete()

    def _update_variants(self, product, variants_data):
        existing_variants = {v.id: v for v in product.variants.all()}
        kept_variant_ids = []

        for v_data in variants_data:
            v_id = v_data.get('id')
            sizes_data = v_data.pop('sizes', [])
            images_data = v_data.pop('images', [])

            if v_id and v_id in existing_variants:
                variant = existing_variants[v_id]
                for key, value in v_data.items():
                    setattr(variant, key, value)
                variant.save()
                kept_variant_ids.append(v_id)
            else:
                if 'id' in v_data: del v_data['id']
                v_data['product'] = product
                variant = ProductVariant.objects.create(**v_data)
                kept_variant_ids.append(variant.id)

            # Update nested sizes and images for this variant
            self._update_nested_relation(variant, sizes_data, 'sizes', SizeVariant, 'variant')
            self._update_nested_relation(variant, images_data, 'images', ProductVariantImage, 'variant')

        # Delete removed variants
        for v_id, variant in existing_variants.items():
            if v_id not in kept_variant_ids:
                variant.delete()

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
                 'mrp', 'discount_percentage', 'stock', 'is_active', 'category_name','key_features', 
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
    variant = ProductVariantSerializer(read_only=True, allow_null=True)
    varient_size = ProductSizeVariantSerializer(read_only=True, allow_null=True)  # FIX

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
        total = Decimal(0)
        for item in obj.items.all():
            if item.varient_size:  # ✔ Correct name now
                price = item.varient_size.get_price
            else:
                price = item.product.get_price
            total += Decimal(price) * item.quantity
        return total


    

class AddToCartSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    variant_id = serializers.IntegerField(required=True)  # still needed (color)
    size_variant_id = serializers.IntegerField(required=True)  # NEW
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
    size_variant = ProductSizeVariantSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = '__all__'



class TrackingScanSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = TrackingScan
        fields = '__all__'

class OrderTrackingSerializer(serializers.ModelSerializer):
    scans = TrackingScanSerializer(many=True,read_only=True)
    
    class Meta:
        model = OrderTracking
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    is_returnable = serializers.SerializerMethodField()
    is_replaceable = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = '__all__'

    def get_is_returnable(self, obj):
        delivery_date = obj.order.delivery_date
        return_period = obj.product.return_period

        if obj.product.is_returnable and delivery_date:
    
            now = timezone.now()
            if (now - delivery_date).days <= return_period:
                return True
        return False

    def get_is_replaceable(self, obj):
        delivery_date = obj.order.delivery_date
        replace_period = obj.product.replace_period

        if obj.product.is_replaceable and delivery_date:
            
            now = timezone.now()
            if (now - delivery_date).days <= replace_period:
                return True
        return False

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(read_only=True,many=True)
    tracking = OrderTrackingSerializer(read_only=True)
    class Meta:
        model = Order
        fields = '__all__'



class PaymentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='order.user.username')
    order_number = serializers.CharField(source='order.order_number')
    class Meta:

        model = Payment
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        exclude = ['password','is_staff','is_superuser','is_active','last_login','user_type','groups','user_permissions','profile_image']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'



from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password



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
        fields = ['id', 'user',"contact_person_number","contact_person_name" ,'address_line1', 'address_line2', 'city', 'state','country', 'postal_code','type_of_address', 'phone', 'is_default', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, data):
        # Ensure only one default address per user
        if data.get('is_default'):
            user = self.context['request'].user
            if ShippingAddress.objects.filter(user=user, is_default=True).exclude(id=self.instance.id if self.instance else None).exists():
                raise serializers.ValidationError({"is_default": "User already has a default address."})
        return data
