from django.db import models
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
from dashboard.services.email import send_order_mail 
import logging

logger = logging.getLogger(__name__)



class AlphaNumericFieldfive(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs["max_length"] = 7  # Set fixed max_length for alphanumeric field
        super().__init__(*args, **kwargs)

    @staticmethod
    def generate_alphanumeric():
        alphanumeric = "".join(
            random.choices(string.ascii_letters + string.digits, k=7)
        )
        return alphanumeric.upper()

class CustomUser(AbstractUser):

    USER_TYPES = (
        ('customer', 'customer'),
        ('admin', 'admin'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='customer')
    email = models.EmailField( blank=True, null=True)
    phone = models.CharField(max_length=15, unique=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']  # if needed
    def __str__(self):
        return f"{self.username}" or f"{self.phone}"

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
    replace_period = models.PositiveIntegerField(default=7)  # days
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

    def save(self, *args, **kwargs):
        self.name = self.color_name.title()  # Auto Title Case conversion
        super(ProductVariant, self).save(*args, **kwargs)

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
        ordering = ['created_at']

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
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
        ('Refunded', 'Refunded'),
        ("Exchanged", "Exchanged"),
        ('Ready to Ship', 'Ready to Ship')
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    order_number =  AlphaNumericFieldfive(unique=True,max_length=20, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='Pending')
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
        is_new_order = self.pk is None  # check if order is new
        
        # Generate order_number if not already set
        if not self.order_number:
            self.order_number = self.generate_unique_order_number()

        # ✅ Set default delivery date only if not already set
        if not self.delivery_date:
            # Use current datetime as base
            base_datetime = self.created_at if self.created_at else timezone.now()
            self.delivery_date = base_datetime + timedelta(days=7)

        super().save(*args, **kwargs)  # save first, to get pk    
        
        

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
        return f"{self.order.order_number} - {self.product.name} - {self.variant} - {self.size_variant} x {self.quantity}"
    
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

    label_file = models.FileField(upload_to="shipping_labels/", null=True, blank=True)

    raw_data = models.JSONField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.awb_number} ({self.current_status})"

class TrackingScan(models.Model):
    tracking = models.ForeignKey(OrderTracking, on_delete=models.CASCADE, related_name="scans")
    return_request = models.ForeignKey("ReturnRequest", null=True, blank=True, on_delete=models.CASCADE, related_name="scans")
    status = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True, null=True)
    scan_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("scan_time",)

    def __str__(self):
        return f"{self.status} @ {self.scan_time}"


class Payment(models.Model):
    PAYMENT_STATUS = (
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
        ('Cancelled', 'Cancelled'),
        ('Refunded', 'Refunded'),
    )
    
    PAYMENT_METHODS = (
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('PayPal', 'PayPal'),
        ('Stripe', 'Stripe'),
        ('Razorpay', 'Razorpay'),
        ('Cash on Delivery', 'Cash on Delivery'),
    )
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='Pending')
    transaction_id = models.CharField(max_length=200, blank=True, null=True)
    payment_id = models.CharField(max_length=200, blank=True, null=True)  # e.g., Razorpay payment_id
    signature_id = models.CharField(max_length=200, blank=True, null=True)  # e.g., Razorpay signature
    gateway_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def save(self, *args, **kwargs):
        is_new_payment = self.pk is None
        old_status = None

        if not is_new_payment:
            old_status = Payment.objects.get(pk=self.pk).status

        super().save(*args, **kwargs)

        # ✅ Only send mail when status changes to 'Completed'
        if (is_new_payment and self.status == 'Completed') or (old_status != self.status and self.status == 'Completed'):
            try:
                send_order_mail(
                    subject=f"Order #{self.order.order_number} Placed Successfully",
                    to_email=self.order.email,
                    template_name='emails/order_success.html',
                    context={
                        'user': self.order.user,
                        'order': self.order
                    }
                )
            except Exception as e:
                logger.error(f"Error sending order success email for Order #{self.order.order_number}: {e}")

    def __str__(self):
        return f"Payment for Order {self.order.order_number}"


# models.py (add these)

from decimal import Decimal

class ReturnRequest(models.Model):
    TYPE_CHOICES = (('Return','Return'), ('Exchange','Exchange'))
    STATUS_CHOICES = (
        ('Requested','Requested'),
        ('Approved','Approved'),
        ('Rejected','Rejected'),
        ('Received','Received'),        # customer sent item back / courier scan
        ('Inspected','Inspected'),
        ('Refunded','Refunded'),
        ('Exchanged','Exchanged'),
        ('Completed','Completed'),
        ('Cancelled','Cancelled'),
    )

    order_item = models.ForeignKey('OrderItem', on_delete=models.CASCADE, related_name='returns')
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE)
    request_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    pickup_awb = models.CharField(max_length=100, null=True, blank=True)  # Delhivery reverse pickup AWB
    quantity = models.PositiveIntegerField(default=1)  # support partial returns
    reason = models.TextField(blank=True, null=True)
    images = models.JSONField(blank=True, null=True)  # optional: photos uploaded by user
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    admin_note = models.TextField(blank=True, null=True)
    admin_by = models.ForeignKey('CustomUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='handled_returns')
    admin_action_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    exchange_for_variant = models.ForeignKey('SizeVariant', null=True, blank=True, on_delete=models.SET_NULL)  # if exchange
    exchange_created_order = models.ForeignKey('Order', null=True, blank=True, on_delete=models.SET_NULL, related_name='exchange_orders')

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"Return #{self.id} for {self.order_item}"


class Refund(models.Model):
    STATUS = (('Initiated','Initiated'),('Processing','Processing'),('Completed','Completed'),('Failed','Failed'))
    return_request = models.ForeignKey(ReturnRequest, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    gateway_txn_id = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default='Initiated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Refund #{self.id} for Return #{self.return_request.id}"



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
    landmark = models.CharField(max_length=255, blank=True, null=True)
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
    


class PasswordResetOTP(models.Model):
    phone = models.CharField(max_length=15)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=10)