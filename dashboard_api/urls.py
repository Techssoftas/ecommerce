from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardLoginView, DashboardLogoutView, DashboardForgotPasswordView

router = DefaultRouter()
# router.register(r'users', UserViewSet) # Example

urlpatterns = [
    path('login/', DashboardLoginView.as_view(), name='dashboard-login'),
    path('logout/', DashboardLogoutView.as_view(), name='dashboard-logout'),
    path('forgot-password/', DashboardForgotPasswordView.as_view(), name='dashboard-forgot-password'),
    path('', include(router.urls)),
]
