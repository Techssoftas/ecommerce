from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
app_name = 'dashboard'

urlpatterns = [
    # Authentication
    path('login_view/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot_password_view/', views.forgot_password_view, name='forgot_password_view'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # path('auth/forgot-password/', views.forgot_password_view, name='forgot_password'),
    # path('auth/reset-password/', views.reset_password_view, name='reset_password'),
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('mens_products/', views.mens_products, name='mens_products'),
    path('womens_products/', views.womens_products, name='womens_products'),
    path('kids_boys_products/', views.kids_boys_products, name='kids_boys_products'),
    path('kids_girls_products/', views.kids_girls_products, name='kids_girls_products'),
   
    path('product_details/<str:product_id>/', views.product_details, name='product_details'),
    path('products/create/', views.product_create, name='product_create'),
    
    path('mens_product_create/', views.mens_product_create, name='mens_product_create'),

    path('products/<str:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<str:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Product Variants
    path('products/<str:product_id>/variants/create/', views.variant_create, name='variant_create'),
    path('products/<int:product_id>/variants/<int:variant_id>/edit/', views.variant_edit, name='variant_edit'),
    path('products/<int:product_id>/variants/<int:variant_id>/delete/', views.variant_delete, name='variant_delete'),
    
    path("product_image/delete/<int:image_id>/", views.delete_product_image, name="delete_product_image"),

    # Categories
    path('categories/', views.variant_delete, name='category_list'),
    path('add_category/', views.add_category, name='add_category'),

    # Orders
    path('orders_list/', views.orders_list, name='orders_list'),
    path('order_detail/<str:order_number>/', views.order_detail, name='order_detail'),
    path('order_edit/<str:pk>/', views.order_detail, name='order_edit'),
    path('order_delete/<str:order_number>/', views.order_delete, name='order_delete'),
    path('order/<str:order_number>/invoice/', views.download_invoice, name='download_invoice'),
    # Payments
    path('payment_list/', views.payment_list, name='payment_list'),
    
    # Stock Management
    path('stock/', views.stock_management, name='stock_management'),
    path('stock/<int:pk>/update/', views.update_stock, name='update_stock'),
    
    # Customers
    path('customers_list/', views.customers_list, name='customers_list'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', views.CustomerEditView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),
        # Reviews
    path('review/delete/<str:review_id>/', views.delete_review, name='delete_review')
]