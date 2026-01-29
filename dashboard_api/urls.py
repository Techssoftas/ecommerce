from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r"mens-products",MensProductViewSet, basename="mens-products")
router.register(r"womens-products", WomensProductViewSet, basename="womens-products")
router.register(r"boys-products", BoysProductViewSet, basename="boys-products")
router.register(r"girls-products", GirlsProductViewSet, basename="girls-products")

urlpatterns = [
    path("", include(router.urls)),
    path('login/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('logout/', LogoutView.as_view(), name='api_logout'),
]
