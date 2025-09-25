from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
app_name = 'dashboard'

urlpatterns = [
    # Authentication
    path('login_view/', login_view, name='login_view'),
    path('logout/', logout_view, name='logout'),
    path('forgot_password_view/', forgot_password_view, name='forgot_password_view'),
    # path('password-reset/done/', auth_PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    # path('reset/<uidb64>/<token>/', auth_PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    # path('reset/done/', auth_PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # path('auth/forgot-password/', forgot_password_view, name='forgot_password'),
    # path('auth/reset-password/', reset_password_view, name='reset_password'),
    # Dashboard
    path('', dashboard, name='dashboard'),
    
    # Products
    path('products/', product_list, name='product_list'),
    path('mens_products/', mens_products, name='mens_products'),
    path('womens_products/', womens_products, name='womens_products'),
    path('kids_boys_products/', kids_boys_products, name='kids_boys_products'),
    path('kids_girls_products/', kids_girls_products, name='kids_girls_products'),
   
    path('product_details/<str:product_id>/', product_details, name='product_details'),
    path('products/create/', product_create, name='product_create'),
    
    path('mens_product_create/', mens_product_create, name='mens_product_create'),
    path('womens_product_create/', womens_product_create, name='womens_product_create'),
    path('kids_boys_product_create/', kids_boys_product_create, name='kids_boys_product_create'),
    path('kids_girls_product_create/', kids_girls_product_create, name='kids_girls_product_create'),

    path('products/<str:pk>/edit/', product_edit, name='product_edit'),
    path('products/<str:pk>/delete/', product_delete, name='product_delete'),
    
    # Product Variants
    path('products/<str:product_id>/variants/create/', variant_create, name='variant_create'),
    path('products/<int:product_id>/variants/<int:variant_id>/edit/', variant_edit, name='variant_edit'),
    path('products/<int:product_id>/variants/<int:variant_id>/delete/', variant_delete, name='variant_delete'),
    
    path("product_image/delete/<int:image_id>/", delete_product_image, name="delete_product_image"),

    #Variants Size
    path("product/<int:product_id>/variant/size/<int:pk>/edit/", size_variant_edit, name="size_variant_edit"),
    path("product/<int:product_id>/variant/size/<int:pk>/delete/",size_variant_delete,name="size_variant_delete",),
    # Assuming you're using 'dashboard' namespace
    path("variant/image/<int:pk>/delete/", delete_variant_image, name="delete_variant_image"),

    # Categories
    path('categories/', variant_delete, name='category_list'),
    path('add_category/', add_category, name='add_category'),
    path('api_add_category/', api_add_category, name='api_add_category'),

    # Orders
    path('orders_list/', orders_list, name='orders_list'),
    path('order_detail/<str:order_number>/', order_detail, name='order_detail'),
    path('order_edit/<str:pk>/', order_detail, name='order_edit'),
    path('order_delete/<str:order_number>/', order_delete, name='order_delete'),
    path('order/<str:order_number>/invoice/', download_invoice, name='download_invoice'),
    # Payments
    path('payment_list/', payment_list, name='payment_list'),
    
    # Stock Management
    path('stock/', stock_management, name='stock_management'),
    path('stock/<int:pk>/update/', update_stock, name='update_stock'),
    
    # Customers
    path('customers_list/', customers_list, name='customers_list'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', CustomerEditView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', CustomerDeleteView.as_view(), name='customer_delete'),
        # Reviews
    path('review/delete/<str:review_id>/', delete_review, name='delete_review'),
    
    
    path('create-shipping-label/<int:order_id>/', create_shipping_label, name='create_shipping_label'),
    path('create_pickup/<int:order_id>/', create_pickup, name='create_pickup'),
    # path('create-shipping-label/<int:order_id>/', create_shipping_label, name='create_shipping_label'),
    path('download-label/<int:tracking_id>/', download_shipping_label, name='download_shipping_label'),
    path('track-order/<int:order_id>/', track_order, name='track_order'),



]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)