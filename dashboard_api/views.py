from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from api.models import Product
from .serializers import ProductSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly,AllowAny
from rest_framework.authtoken.models import Token
from django.db import transaction
from django.contrib.auth import get_user_model
User = get_user_model()

class MensProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny] 
    authentication_classes = []

    def get_queryset(self):
        return Product.objects.filter(is_active=True,subcategory="Mens")
    
class WomensProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Product.objects.filter(subcategory="Womens",is_active=True)
    
class BoysProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Product.objects.filter(subcategory="Kids(Boys)",is_active=True)
    
class GirlsProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Product.objects.filter(subcategory="Kids(Girls)",is_active=True)
    
class CustomAuthToken(ObtainAuthToken):
    """
    Custom API View to return User Token and Details
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'username': user.username,
            'email': user.email,
            'concern_code': user.concern_code if hasattr(user, 'concern_code') else ''
        })

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        return Response({
            "message": "Logged out successfully"
        },status=status.HTTP_200_OK)