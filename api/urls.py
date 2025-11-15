from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import *
from django.conf import settings
from django.conf.urls.static import static

app_name = 'api'


urlpatterns = [
    # JWT Authentication
    path('sendotpview/', SendOTPView.as_view(), name='sendotpview'),
    path('loginverifyotpview/', LoginVerifyOTPView.as_view(), name='loginverifyotpview'),
    
    path('login/', EmailLoginView.as_view(), name='email_login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('set-new-password/', SetNewPasswordView.as_view(), name='set_new_password'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),

    path('logout/', logout_view, name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile_update/', UpdateProfileView.as_view(), name='profile_update'),
    
    # Products
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<str:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    
    path('filter_products/', FilterListView.as_view(), name='filter_products'),
    path('shopfilter/', ShopFilterListView.as_view(), name='shopfilter'),

    # Cart
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/<str:item_id>/', CartView.as_view(), name='cart'),
    # path('add_to_cart/', add_to_cart, name='add_to_cart'),
    # path('cart_update/<str:item_id>/', UpdateCartItemView.as_view(), name='update_cart_item'),
    # path('cart_remove/<str:item_id>/', remove_from_cart, name='remove_from_cart'),
    
    # Wishlist
    path('wishlist/', wishlist_view, name='wishlist'),
    path('add_to_wishlist/',AddToWishlistView.as_view(), name='add_to_wishlist'),
    path('wishlist_remove/<str:product_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    
    # Orders
    path('orders/', OrderApiView.as_view(), name='order_list'),# For GET/POST
    path('order_detail/<str:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('pending_orders/', PendingOrderApiView.as_view(), name='pending_order_list'),# For GET/POST
    path('orders/<int:order_id>/', OrderApiView.as_view(), name='order_update'),# For PUT
    path('buy_now/', BuyNowCheckoutView.as_view(), name='buy_now'),
    path('cart_checkout/', CartCheckoutView.as_view(), name='cart_checkout'),

    # path('create_order/', create_order, name='create_order'),
    # path('verify_payment/', verify_payment, name='verify_payment'),
       
    path('create-order/', create_order, name='create_order'),
        
    path('initiate_payment/', initiate_payment, name='initiate_payment'),
    path('confirm_order/', confirm_order, name='confirm_order'),
    path('cod_order_create/', cod_order_create, name='cod_order_create'),
    
    
    path('create_return_request/', ReturnRequestCreateView.as_view(), name='create_return_request'),


    path('shipping-address/', ShippingAddressListCreateView.as_view(), name='shipping-addresses'),
    path('shipping-address/<int:pk>/', ShippingAddressDetailView.as_view(), name='shipping-address-detail'),
    path("webhooks/delhivery/", delhivery_webhook, name="delhivery-webhook"),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)