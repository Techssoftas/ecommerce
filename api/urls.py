from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import *
from django.conf import settings
from django.conf.urls.static import static

app_name = 'api'


urlpatterns = [
    # JWT Authentication
    path('login/', EmailLoginView.as_view(), name='email_login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('logout/', logout_view, name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile_update/', UpdateProfileView.as_view(), name='profile_update'),
    
    # Products
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<str:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    
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
    path('buy_now/', SingleProductPurchaseAPIView.as_view(), name='buy_now'),

    path('shipping-address/', ShippingAddressListCreateView.as_view(), name='shipping-addresses'),
    path('shipping-address/<int:pk>/', ShippingAddressDetailView.as_view(), name='shipping-address-detail'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)