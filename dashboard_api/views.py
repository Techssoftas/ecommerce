from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from api.models import CustomUser, PasswordResetOTP
import random
import http.client
import json
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

class DashboardLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        password = request.data.get("password")

        if not phone or not password:
            return Response({"error": "Phone number and password required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=phone, password=password) # USERNAME_FIELD is phone in CustomUser

        if user is not None:
            if user.user_type == 'admin':
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    "message": "Login Successful",
                    "token": token.key,
                    "user_type": user.user_type,
                    "username": user.username or user.phone
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Unauthorized: Admin access required"}, status=status.HTTP_403_FORBIDDEN)
        
        return Response({"error": "Invalid Phone number or Password"}, status=status.HTTP_401_UNAUTHORIZED)

class DashboardLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            request.user.auth_token.delete()
            return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Something went wrong"}, status=status.HTTP_400_BAD_REQUEST)

class DashboardForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
             return Response({'error': 'Phone number required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(phone=phone)
            # Optional: Check if admin? User didn't specify strict check for forgot password, but good practice if only for dashboard.
            # But let's keep it open or check admin if it's strictly dashboard api.
            if user.user_type != 'admin':
                 return Response({"error": "Unauthorized: Only admins can reset password here"}, status=status.HTTP_403_FORBIDDEN)

            otp = str(random.randint(100000, 999999))

            # Delete old OTPs
            PasswordResetOTP.objects.filter(phone=phone).delete()
            # Create new OTP
            PasswordResetOTP.objects.create(phone=phone, otp=otp)

            # Send SMS (Reusing logic logic or simplified)
            formatted_phone = phone
            if not phone.startswith('91'):
                formatted_phone = '91' + phone
            
            if self.send_otp_sms(formatted_phone, otp):
                return Response({
                    'message': 'OTP sent successfully',
                    'phone': formatted_phone
                }, status=status.HTTP_200_OK)
            else:
                 return Response({'error': 'Failed to send OTP'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def send_otp_sms(self, phone, otp):
        try:
            conn = http.client.HTTPSConnection("control.msg91.com")
            payload = {
                "template_id": "6905a16bfe379201c74c5e32", # Using ID from api/views.py
                "short_url": "1",
                "recipients": [{"mobiles": phone, "number": otp}]
            }
            headers = {
                'accept': "application/json",
                'authkey': "470722Ae1mHUuQ3W6902fc0fP1", # Using key from api/views.py
                'content-type': "application/json"
            }
            conn.request("POST", "/api/v5/flow", json.dumps(payload), headers)
            res = conn.getresponse()
            data = res.read()
            response_data = json.loads(data.decode("utf-8"))
            return response_data.get('type') == 'success'
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            return False

from rest_framework import viewsets
from api.models import *
from api.serializers import PaymentSerializer,UserSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by('-created_at')
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    permission_classes = [permissions.IsAuthenticated]
    
class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.filter(user_type='customer').order_by('-created_at')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

from api.models import Product
from api.serializers import DashboardProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = DashboardProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'subcategory', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']

from api.models import Order, ReturnRequest
from api.serializers import OrderSerializer, ReturnRequestSerializer
from rest_framework.decorators import action

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment__payment_method', 'payment__status']
    search_fields = ['order_number', 'user__username', 'user__phone']
    ordering_fields = ['created_at', 'total_amount']

    @action(detail=False, methods=['get'])
    def exchanges(self, request):
        """
        Returns orders that have at least one exchange request.
        """
        queryset = self.get_queryset().filter(items__returns__request_type='Exchange').distinct()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class ReturnRequestViewSet(viewsets.ModelViewSet):
    queryset = ReturnRequest.objects.all().order_by('-requested_at')
    serializer_class = ReturnRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['request_type', 'status']
    search_fields = ['order_item__order__order_number', 'user__username', 'user__phone']
    ordering_fields = ['requested_at']
