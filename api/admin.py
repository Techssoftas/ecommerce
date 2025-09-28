from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

admin.site.register(ReviewImage)
admin.site.register(ShippingAddress)
admin.site.register(Payment)
admin.site.register(Category)
admin.site.register(SizeVariant)
admin.site.register(ProductVariantImage)
admin.site.register(OrderTracking)
admin.site.register(TrackingScan)
admin.site.register(ReturnRequest)
# @admin.register(CustomUser)
# class CustomUserAdmin(UserAdmin):
#     list_display = ('username', 'email', 'user_type', 'is_active', 'date_joined')
#     list_filter = ('user_type', 'is_active', 'date_joined')
#     fieldsets = UserAdmin.fieldsets + (
#         ('Additional Info', {
#             'fields': ('user_type', 'phone', 'address', 'date_of_birth', 'profile_image')
#         }),
#     )

# @admin.register(Category)
# class CategoryAdmin(admin.ModelAdmin):
#     list_display = ('name', 'is_active', 'created_at')
#     list_filter = ('is_active', 'created_at')
#     search_fields = ('name',)

# class ProductImageInline(admin.TabularInline):
#     model = ProductImage
#     extra = 1

# class ProductVariantInline(admin.TabularInline):
#     model = ProductVariant
#     extra = 1

# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('name', 'category', 'price', 'stock', 'is_active', 'created_at')
#     list_filter = ('category', 'is_active', 'created_at')
#     search_fields = ('name', 'sku')
#     inlines = [ProductImageInline, ProductVariantInline]

# @admin.register(Order)
# class OrderAdmin(admin.ModelAdmin):
#     list_display = ('order_number', 'user', 'status', 'total_amount', 'created_at')
#     list_filter = ('status', 'created_at')
#     search_fields = ('order_number', 'user__username')

# @admin.register(Payment)
# class PaymentAdmin(admin.ModelAdmin):
#     list_display = ('order', 'payment_method', 'amount', 'status', 'created_at')
#     list_filter = ('payment_method', 'status', 'created_at')
#     search_fields = ('order__order_number', 'transaction_id')

admin.site.register(ProductImage)
admin.site.register(ProductVariant)
admin.site.register(Product)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(CustomUser)
admin.site.register(Wishlist)
admin.site.register(OrderItem)
admin.site.register(Order)
admin.site.register(Review)