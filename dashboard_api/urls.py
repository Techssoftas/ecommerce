from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardLoginView, DashboardLogoutView, DashboardForgotPasswordView, PaymentViewSet, UserViewSet, ProductViewSet

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='dashboard-payments')
router.register(r'customers', UserViewSet, basename='dashboard-customers')
router.register(r'products', ProductViewSet, basename='dashboard-products')

urlpatterns = [
    path('login/', DashboardLoginView.as_view(), name='dashboard-login'),
    path('logout/', DashboardLogoutView.as_view(), name='dashboard-logout'),
    path('forgot-password/', DashboardForgotPasswordView.as_view(), name='dashboard-forgot-password'),
    path('', include(router.urls)),
]
