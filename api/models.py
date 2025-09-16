from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import Group, AbstractUser
from django.db import models, connection
from math import radians, sin, cos, sqrt, atan2
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import BaseUserManager
import random
import string
from django.core.mail import send_mail
from collections import defaultdict
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, F, DecimalField

class AlphaNumericFieldfive(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 5  # Set fixed max_length for alphanumeric field
        super().__init__(*args, **kwargs)

    @staticmethod
    def generate_alphanumeric():
        alphanumeric = "".join(
            random.choices(string.ascii_letters + string.digits, k=5)
        )
        return alphanumeric.upper()

class CustomUser(AbstractUser):

    USER_TYPES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='customer')
    email = models.EmailField(unique=True) 
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # if needed
    def __str__(self):
        return f"{self.username}"

class Category(models.Model):
    SUB_CATEGORY = (
        ('Mens', 'Mens'),
        ('Womens', 'Womens'),
        ('Kids(Boys)', 'Kids(Boys)'),
        ('Kids(Girls)', 'Kids(Girls)'),
        
    )
      
    name = models.CharField(max_length=100)
    subcategory = models.CharField(max_length=100,choices=SUB_CATEGORY, default='Mens')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ('name', 'subcategory')  # Uniqueness here
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.subcategory})"

    def save(self, *args, **kwargs):
        self.name = self.name.title()  # Auto Title Case conversion
        super(Category, self).save(*args, **kwargs)


class Product(models.Model):
    CONDITION_CHOICES = (
        ('new', 'New'),
        ('refurbished', 'Refurbished'),
        ('used', 'Used'),
    )
    
    AVAILABILITY_STATUS = (
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('limited_stock', 'Limited Stock'),
        ('pre_order', 'Pre Order'),
        ('discontinued', 'Discontinued'),
    )
    SUB_CATEGORY = (
        ('Mens', 'Mens'),
        ('Womens', 'Womens'),
        ('Kids(Boys)', 'Kids(Boys)'),
        ('Kids(Girls)', 'Kids(Girls)'),
        
    )
    
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, blank=True, null=True)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    fabric = models.CharField(max_length=100, blank=True, null=True)
    occasion = models.CharField(max_length=100, blank=True, null=True)
    short_description = models.CharField(max_length=500, blank=True)
    description = models.TextField()
    specifications = models.JSONField(default=dict, blank=True)  # Store detailed specs
    key_features = models.JSONField(default=list, blank=True)  # Array of key features
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.CharField(max_length=100,choices=SUB_CATEGORY, default='Mens')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Maximum Retail Price
    stock = models.PositiveIntegerField(default=0)
    minimum_order_quantity = models.PositiveIntegerField(default=1)
    maximum_order_quantity = models.PositiveIntegerField(blank=True, null=True)
    sku = models.CharField(max_length=100, unique=True)
    barcode = models.CharField(max_length=50, blank=True, null=True)
    hsn_code = models.CharField(max_length=20, blank=True, null=True)  # HSN code for tax
    
    # Physical attributes
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)  # in kg
    dimensions_length = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)  # in cm
    dimensions_width = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)  # in cm
    dimensions_height = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)  # in cm
    
    # Product condition and availability
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_STATUS, default='in_stock')
    
    # SEO and marketing
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)  # Array of tags
    
    # Shipping and delivery
    is_free_shipping = models.BooleanField(default=False)
    shipping_weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    delivery_time_min = models.PositiveIntegerField(default=1)  # minimum delivery days
    delivery_time_max = models.PositiveIntegerField(default=7)  # maximum delivery days
    
    # Product flags
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_deal_of_day = models.BooleanField(default=False)
    is_returnable = models.BooleanField(default=False)
    is_replaceable = models.BooleanField(default=False)
    is_cod_available = models.BooleanField(default=False)  # Cash on Delivery
    
    # Warranty and support
    warranty_period = models.CharField(max_length=100, blank=True)  # e.g., "1 Year", "6 Months"
    warranty_type = models.CharField(max_length=100, blank=True)  # e.g., "Manufacturer", "Seller"
    warranty_description = models.TextField(blank=True)
    
    # Return policy
    return_period = models.PositiveIntegerField(default=7)  # days
    return_policy = models.TextField(blank=True)
    
    # Ratings and reviews
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Sales data
    total_sold = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional dates
    launch_date = models.DateTimeField(blank=True, null=True)
    last_restocked = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.id}"
    
    def save(self, *args, **kwargs):
        # Calculate discount percentage
        if self.mrp and self.price:
            self.discount_percentage = (
                (Decimal(self.mrp) - Decimal(self.price)) / Decimal(self.mrp)
            ) * 100
        super().save(*args, **kwargs)
    
    @property
    def get_price_range(self):
        """Get price range for product including variants"""
        prices = [self.get_price]
        
        # Add variant prices
        variant_prices = [s.get_price for v in self.variants.filter(is_active=True) for s in v.sizes.all()]
        if variant_prices:
            prices.extend(variant_prices)
        
        min_price = min(prices)
        max_price = max(prices)
        
        if min_price == max_price:
            return f"₹{min_price}"
        else:
            return f"₹{min_price} - ₹{max_price}"
    
    @property
    def get_price(self):
        """Get base product price"""
        return self.discount_price if self.discount_price else self.price
    
    @property
    def get_savings(self):
        if self.mrp and self.get_price:
            return self.mrp - self.get_price
        return 0
    
    @property
    def is_in_stock(self):
        return self.stock > 0 and self.availability_status == 'in_stock'
    
    @property
    def is_low_stock(self):
        return self.stock <= 10
    
    @property
    def stock_status(self):
        if self.stock == 0:
            return 'Out of Stock'
        elif self.stock <= 5:
            return 'Only few left'
        elif self.stock <= 10:
            return 'Limited Stock'
        else:
            return 'In Stock'
    
    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first()
    
    @property
    def rating_distribution(self):
        """Get rating distribution for 1-5 stars"""
        from django.db.models import Count
        return self.reviews.values('rating').annotate(count=Count('rating')).order_by('rating')
    
   


    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['brand', 'is_active']),
            models.Index(fields=['price']),
            models.Index(fields=['average_rating']),
            models.Index(fields=['total_sold']),
        ]

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.product.id} "

class ProductVariant(models.Model):
    """Main variant (e.g., color)"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color_name = models.CharField(max_length=100)  # Example: Red, Blue
    hex_color_code = models.CharField(max_length=7, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'color_name')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.color_name}"
    
    

class ProductVariantImage(models.Model):
    """Multiple images for each color variant"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='variants/')
    is_default = models.BooleanField(default=False)  # optional: mark main image

    def __str__(self):
        return f"Image of {self.variant}"


class SizeVariant(models.Model):
    """Each size inside a color variant"""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='sizes')
    size = models.CharField(max_length=50)  # e.g. S, M, L, XL
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('variant', 'size')

    def __str__(self):
        return f"{self.variant} - {self.size}"
    @property
    def get_price(self):
        """Get the effective selling price"""
        return self.price if self.price else self.mrp
    
    @property
    def get_savings(self):
        """Calculate savings from MRP"""
        if self.mrp and self.get_price:
            return self.mrp - self.get_price
        return 0
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage"""
        if self.mrp and self.price:
            return ((self.mrp - self.get_price) / self.mrp) * 100
        return 0
    
    @property
    def is_in_stock(self):
        """Check if variant is in stock"""
        return self.stock > 0 and self.is_active

class Cart(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart - {self.user.username}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def total_stock(self):
        return sum(size.stock for v in self.variants.all() for size in v.sizes.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, blank=True, null=True)
    varient_size = models.ForeignKey(SizeVariant, on_delete=models.CASCADE, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def subtotal(self):
        price = self.product.get_price
        if self.variant:
            price = self.varient_size.get_price if self.varient_size else self.product.get_price
        return price * self.quantity

class Wishlist(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, blank=True, null=True)
    size_variant  = models.ForeignKey(SizeVariant, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product', 'variant', 'size_variant')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

class Order(models.Model):
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    order_number =  AlphaNumericFieldfive(unique=True, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    source = models.CharField(max_length=10,choices=(('cart', 'Cart'), ('buynow', 'Buy Now')),default='cart')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.ForeignKey('api.ShippingAddress', on_delete=models.SET_NULL, null=True, related_name='orders')
    billing_address = models.TextField()
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    notes = models.TextField(blank=True)
    delivery_date = models.DateTimeField(blank=True, null=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def generate_unique_order_number(self):
        while True:
            code = AlphaNumericFieldfive.generate_alphanumeric()
            if not Order.objects.filter(order_number=code).exists():
                return code
            
    def save(self, *args, **kwargs):
        
        # Generate order_number if not already set
        if not self.order_number:
            self.order_number = self.generate_unique_order_number()

        # ✅ Set default delivery date only if not already set
        if not self.delivery_date:
            # Use current datetime as base
            base_datetime = self.created_at if self.created_at else timezone.now()
            self.delivery_date = base_datetime + timedelta(days=7)
            
        # Check if status has changed
        if self.pk:  # If order already exists
            old_order = Order.objects.get(pk=self.pk)
            if old_order.status != self.status:
                # Send notification to user
                send_mail(
                    subject=f'Order {self.order_number} Status Update',
                    message=f'Your order status has changed to: {self.get_status_display()}',
                    from_email='no-reply@yourstore.com',
                    recipient_list=[self.email],
                    fail_silently=True,
                )

        super().save(*args, **kwargs)

    @property
    def total_mrp(self):
        return self.items.aggregate(
            total=Sum(F('quantity') * F('size_variant__mrp'), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'] or Decimal('0.00')
    @property
    def total_selling(self):
        return self.items.aggregate(
            total=Sum(F('quantity') * F('size_variant__price'), output_field=DecimalField(max_digits=10, decimal_places=2))
        )['total'] or Decimal('0.00')
    @property
    def total_discount(self):
        return (self.total_mrp or 0) - (self.total_selling or 0)    
    @property
    def estimated_delivery_date(self):
        if self.status == "delivered":
            return self.updated_at.date()
        first_item = self.items.first()
        if first_item:
            return (self.created_at.date() + timedelta(days=first_item.product.delivery_time_max))
        return self.created_at.date()        
    def __str__(self):
        return f"Order {self.order_number}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, blank=True, null=True)
    size_variant = models.ForeignKey(SizeVariant, on_delete=models.CASCADE, blank=True, null=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def subtotal(self):
        if self.size_variant:
            return Decimal(self.quantity) * self.size_variant.mrp
        return Decimal('0.00')
    
    @property
    def subselling_price(self):
        if self.size_variant:
            return Decimal(self.quantity) * self.size_variant.get_price
        return Decimal('0.00')

from django.db import models
from django.utils import timezone

class OrderTracking(models.Model):
    order = models.OneToOneField("Order", on_delete=models.CASCADE, related_name="tracking")
    awb_number = models.CharField(max_length=50, unique=True)
    current_status = models.CharField(max_length=100, blank=True, null=True)
    last_event_id = models.CharField(max_length=200, blank=True, null=True)  # idempotency
    raw_data = models.JSONField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.awb_number} ({self.current_status})"

class TrackingScan(models.Model):
    tracking = models.ForeignKey(OrderTracking, on_delete=models.CASCADE, related_name="scans")
    status = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True, null=True)
    scan_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("scan_time",)

    def __str__(self):
        return f"{self.status} @ {self.scan_time}"


class Payment(models.Model):
    PAYMENT_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_METHODS = (
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('cash_on_delivery', 'Cash on Delivery'),
    )
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    transaction_id = models.CharField(max_length=200, blank=True, null=True)
    gateway_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment for Order {self.order.order_number}"

class Review(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product')
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating}/5)"
    
class ReviewImage(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='review_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.review.title}"
    
    
class ShippingAddress(models.Model):
    ADDRESS_TYPE =(
        ('home', 'Home'),
        ('office', 'Office'),
        ('other', 'Other')
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='shipping_addresses')
    type_of_address = models.CharField(max_length=20, choices=ADDRESS_TYPE, default='home')
    state = models.CharField(max_length=100, blank=True, null=True)
    contact_person_name = models.CharField(max_length=100, blank=True, null=True)
    contact_person_number = models.CharField(max_length=100, blank=True, null=True)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Shipping Addresses"

    def __str__(self):
        return f"{self.user.username} - {self.address_line1}, {self.city}"