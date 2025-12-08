from rest_framework import generics, status, permissions,viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import *
from .serializers import *
from rest_framework.generics import RetrieveAPIView,UpdateAPIView
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from api.models import CustomUser,PasswordResetOTP
from api.utils import send_sms
from api.utils import send_order_sms
from django.conf import settings
import http.client

import logging
logger = logging.getLogger(__name__)

# Authentication Views

import random, http.client, json
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        raw_phone = request.data.get('phone')
        print("Raw phone:", raw_phone)

        if not raw_phone:
            return Response({'error': 'Phone number required'}, status=400)

        # phone clean pannrom
        phone = str(raw_phone).strip().replace('+', '').replace(' ', '').replace('-', '')
        print("Clean phone:", phone)

        # India number assume (91)
        if phone.startswith('91') and len(phone) == 12 and phone.isdigit():
            full_mobile = phone
        elif len(phone) == 10 and phone.isdigit():
            full_mobile = '91' + phone
        else:
            return Response({'error': 'Invalid phone number format'}, status=400)

        # 6-digit OTP
        otp = random.randint(100000, 999999)
        key = f"otp_{str(full_mobile)}"
        print("CACHE SET KEY:", key, "OTP:", otp)
        cache.set(key, otp, timeout=300)
        try:
            conn = http.client.HTTPSConnection("api.msg91.com")
            print('full_mobile',full_mobile)
            # Flow / template: ##var## is your login OTP ...
            payload = {
                "flow_id": "6933ead2feb44e75700baf8e",  # MSG91 template/flow ID
                "sender": "MTEXTE",                    # MSG91 sender ID (DLT verified)
                "mobiles": full_mobile,                # 91XXXXXXXXXX
                "var": str(otp)                        # maps to ##var## in template
            }

            headers = {
                "accept": "application/json",
                "authkey": "470722Ae1mHUuQ3W6902fc0fP1",       # replace with real authkey
                "content-type": "application/json"
            }

            print("Final payload:", payload)
            conn.request("POST", "/api/v5/flow", json.dumps(payload), headers)
            res = conn.getresponse()
            body = res.read().decode()
            print("Status:", res.status)
            print("Body:", body)

            # optional parse
            try:
                resp_json = json.loads(body)
                print("Parsed:", resp_json)
            except Exception:
                pass

        except Exception as e:
            print("⚠️ OTP Send Failed:", e)
            return Response({'error': 'OTP send failed'}, status=500)

        return Response(
            {'message': f'OTP sent successfully to {full_mobile}'},
            status=200
        )
    

class LoginVerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        raw_phone = str(request.data.get('phone')).strip()
        otp = int(str(request.data.get('otp')).strip())
        # 🆕 extra fields for cart / wishlist action
        action = request.data.get('action')  # 'cart' or 'wishlist' or None
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        size_variant_id = request.data.get('size_variant_id')
        quantity = int(request.data.get('quantity') or 1)

        if not raw_phone:
            return Response({'error': 'Phone number required'}, status=400)

        # phone clean pannrom
        phone = str(raw_phone).strip().replace('+', '').replace(' ', '').replace('-', '')
        print("Clean phone:", phone)

        # India number assume (91)
        if phone.startswith('91') and len(phone) == 12 and phone.isdigit():
            full_mobile = phone
        elif len(phone) == 10 and phone.isdigit():
            full_mobile = '91' + phone
        else:
            return Response({'error': 'Invalid phone number format'}, status=400)
        
        print("Full mobile for login:", full_mobile)
        # OTP check
        cache_key = f"otp_{full_mobile}"
        print("CACHE GET KEY:", cache_key)

        saved_otp = cache.get(cache_key)
        print("Saved OTP:", saved_otp, type(saved_otp))
        print("Provided OTP:", otp, type(otp))
        if saved_otp is None:
            return Response({'error': 'OTP expired or not found'}, status=status.HTTP_400_BAD_REQUEST)

        if int(saved_otp) != int(otp):
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        # OTP valid → delete cache
        cache.delete(cache_key)

        # Check if user exists or not
        user, created = User.objects.get_or_create(phone=phone)

        if created:
            # If new user, set defaults like in your RegisterView
            username = phone  # or generate any default username
            user.username = username
            user.first_name = username
            user.set_password(phone)  # optional default password
            user.save()

            # ✅ Send Welcome SMS (same as RegisterView logic)
            try:
                print("📱 Sending Welcome SMS to:", phone)
                mobile = str(phone).strip()

                # 91 prefix check panni add panrom
                if not mobile.startswith('91'):
                    if len(mobile) == 10 and mobile.isdigit():
                        mobile = '91' + mobile
                    else:
                        print(f"⚠️ Invalid phone format: {mobile}")
                        raise ValueError("Invalid phone number format")

                conn = http.client.HTTPSConnection("control.msg91.com")

                payload = {
                    "template_id": '69059476c859393d1f62a803',  # same registration template
                    "short_url": "1",
                    "recipients": [
                        {
                            "mobiles": mobile,
                            "var": user.first_name
                        }
                    ]
                }

                headers = {
                    'accept': "application/json",
                    'authkey': '470722Ae1mHUuQ3W6902fc0fP1',  # MSG91 authkey
                    'content-type': "application/json"
                }

                conn.request("POST", "/api/v5/flow", json.dumps(payload), headers)
                res = conn.getresponse()
                data = res.read()
                response_data = json.loads(data.decode("utf-8"))

                print("📲 MSG91 Response:", response_data)

                if response_data.get('type') == 'success':
                    print("✅ Welcome SMS sent successfully!")
                else:
                    print(f"⚠️ SMS failed: {response_data.get('message', 'Unknown error')}")

            except Exception as e:
                print(f"⚠️ SMS sending failed: {e}")

        # Create token for both new/existing user
        token, _ = Token.objects.get_or_create(user=user)

        # 5) Action handle panna (cart / wishlist)
        action_result = None

        # ⭐ CART ACTION
        if action == "cart" and product_id:
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_400_BAD_REQUEST)

            variant = None
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
                except ProductVariant.DoesNotExist:
                    return Response({'error': 'Variant not found'}, status=status.HTTP_400_BAD_REQUEST)

            size_variant = None
            if size_variant_id:
                try:
                    size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)
                except SizeVariant.DoesNotExist:
                    return Response({'error': 'Size variant not found'}, status=status.HTTP_400_BAD_REQUEST)

            # User oda cart get_or_create
            cart, _ = Cart.objects.get_or_create(user=user)

            # Same product + variant + size irundha quantity increase panna
            item, item_created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variant=variant,
                varient_size=size_variant,
                defaults={'quantity': quantity}
            )

            if not item_created:
                item.quantity += quantity
                item.save()

            action_result = {
                "type": "cart",
                "message": "Added to cart successfully",
                "cart_total_items": cart.total_items,
                "cart_total_price": float(cart.total_price or 0),
            }

        # ⭐ WISHLIST ACTION
        if action == "wishlist" and product_id:
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_400_BAD_REQUEST)

            variant = None
            if variant_id:
                try:
                    variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
                except ProductVariant.DoesNotExist:
                    return Response({'error': 'Variant not found'}, status=status.HTTP_400_BAD_REQUEST)

            size_variant = None
            if size_variant_id:
                try:
                    size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)
                except SizeVariant.DoesNotExist:
                    return Response({'error': 'Size variant not found'}, status=status.HTTP_400_BAD_REQUEST)

            wishlist_obj, _ = Wishlist.objects.get_or_create(
                user=user,
                product=product,
                variant=variant,
                size_variant=size_variant,
            )

            action_result = {
                "type": "wishlist",
                "message": "Added to wishlist",
                "product_id": product.id,
                "variant_id": variant.id if variant else None,
                "size_variant_id": size_variant.id if size_variant else None,
            }

        return Response({
            'message': 'Login successful' if not created else 'Account created successfully!',
            'token': token.key,
            'user': {
                'username': user.first_name,
                'phone': user.phone,
            },
            'action_result': action_result,
        }, status=status.HTTP_200_OK)

class EmailLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        phone = request.data.get("phone")
        password = request.data.get("password")

        if not phone or not password:
            return Response({"error": "PhoneNumber and password required"}, status=status.HTTP_400_BAD_REQUEST)

        # authenticate will automatically use USERNAME_FIELD = 'email'
        user = authenticate(request, phone=phone, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login Successfully..!",
                "token": token.key,
                'username':user.first_name,
               
            }, status=status.HTTP_200_OK)

        return Response({"error": "Invalid Phonenumber or Password"}, status=status.HTTP_401_UNAUTHORIZED)

class TestProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "Authenticated user", "email": request.user.email})


import http.client
import json
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.conf import settings


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    

    def create(self, request, *args, **kwargs):
        print("RegisterView", request.data)
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # Create token
            token, _ = Token.objects.get_or_create(user=user)

            # ✅ Send welcome SMS - safe with try-except
            try:
                print("User phone:", str(user.phone))
                
                # Phone number ah string ah convert panrom
                mobile = str(user.phone).strip()

                # 91 prefix check panni add panrom
                if not mobile.startswith('91'):
                    # 10 digits iruntha 91 add panrom
                    if len(mobile) == 10 and mobile.isdigit():
                        mobile = '91' + mobile
                    else:
                        print(f"⚠️ Invalid phone format: {mobile}")
                        raise ValueError("Invalid phone number format")

                print(f"📱 Sending Welcome SMS to: {mobile}")

                # MSG91 SMS send panrom
                conn = http.client.HTTPSConnection("control.msg91.com")

                # Payload prepare panrom
                payload = {
                    "template_id": '69059476c859393d1f62a803',  # Registration template ID
                    "short_url": "1",
                    "recipients": [
                        {
                            "mobiles": mobile,
                            "var": user.first_name  # Template la ##var## variable ku value
                        }
                    ]
                }

                # JSON string ah convert panrom
                payload_json = json.dumps(payload)

                # Headers set panrom
                headers = {
                    'accept': "application/json",
                    'authkey': '470722Ae1mHUuQ3W6902fc0fP1' , # MSG91 authkey
                    'content-type': "application/json"
                }

                # API request send panrom
                conn.request("POST", "/api/v5/flow", payload_json, headers)

                # Response vaangurom
                res = conn.getresponse()
                data = res.read()

                # Response decode panni parse panrom
                response_data = json.loads(data.decode("utf-8"))
                
                print(f"📱 MSG91 Response: {response_data}")

                # Success ah send aacha nu check panrom
                if response_data.get('type') == 'success':
                    print(f"✅ Welcome SMS sent to {mobile} successfully!")
                else:
                    print(f"⚠️ SMS sending failed: {response_data.get('message', 'Unknown error')}")

            except Exception as e:
                print(f"⚠️ SMS sending failed: {e}")
                # SMS fail aanalum registration success ah irukkanum

            return Response({
                'token': token.key,
                'user': UserProfileSerializer(user).data,
                'message': 'Account registered successfully!'
            }, status=status.HTTP_201_CREATED)
            
        print("Registration Error:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Logout successfully..!'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def refresh_token_view(request):
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        access_token = token.access_token
        
        return Response({
            'access': str(access_token),
            'message': 'Token refreshed successfully'
        })
    except Exception as e:
        return Response({'error': 'Invalid refresh token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def verify_token_view(request):
    try:
        # If we reach here, the token is valid (JWT middleware validated it)
        return Response({
            'valid': True,
            'user': UserProfileSerializer(request.user).data
        })
    except Exception as e:
        pass
    return Response({'valid': False}, status=status.HTTP_401_UNAUTHORIZED)




class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password changed successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

import random
class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone')

        try:
            user = CustomUser.objects.get(phone=phone)

            otp = str(random.randint(100000, 999999))

            # Old OTPs delete panrom (same phone ku multiple OTP irukatha)
            PasswordResetOTP.objects.filter(phone=phone).delete()

            # New OTP store
            PasswordResetOTP.objects.create(phone=phone, otp=otp)

            print(f"OTP for {phone}: {otp}")
            formatted_phone = phone
            if not phone.startswith('91'):
                formatted_phone = '91' + phone
            
            # MSG91 SMS send function call panrom
            sms_sent = self.send_otp_sms(formatted_phone, otp)
            if sms_sent:
                return Response({
                    'message': 'OTP sent successfully',
                    'phone': formatted_phone
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to send OTP'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except CustomUser.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_400_BAD_REQUEST)

    def send_otp_sms(self, phone, otp):
        """
        MSG91 API use panni SMS send panrom
        """
        try:
            # HTTPS connection create panrom
            conn = http.client.HTTPSConnection("control.msg91.com")

            # Request body prepare panrom
            payload = {
                "template_id": "6905a16bfe379201c74c5e32",  # Ungaloda template ID podunga
                "short_url": "1",  # URL shorten venam na 0
                "recipients": [
                    {
                        "mobiles": phone,  # 91XXXXXXXXXX format la irukkanum
                        "number": otp  # Template la ##OTP## iruntha indha variable pass aagum
                    }
                ]
            }

            # JSON string ah convert panrom
            payload_json = json.dumps(payload)

            # Headers set panrom
            headers = {
                'accept': "application/json",
                'authkey': "470722Ae1mHUuQ3W6902fc0fP1",  # Ungaloda authkey podunga
                'content-type': "application/json"
            }

            # API request send panrom
            conn.request("POST", "/api/v5/flow", payload_json, headers)

            # Response vaangurom
            res = conn.getresponse()
            data = res.read()

            # Response decode panni check panrom
            response_data = json.loads(data.decode("utf-8"))
            
            print(f"MSG91 Response: {response_data}")

            # Success ah send aacha nu check panrom
            if response_data.get('type') == 'success':
                return True
            else:
                return False

        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            return False


from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta
from .models import PasswordResetOTP

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = request.data.get('phone')
        otp = request.data.get('otp')
        print("VerifyOTPView",phone,otp)
        try:
            otp_obj = PasswordResetOTP.objects.filter(phone=phone).last()

            if not otp_obj:
                return Response({'error': 'OTP not found'}, status=status.HTTP_400_BAD_REQUEST)

            if otp_obj.is_expired():
                otp_obj.delete()  # delete expired
                return Response({'error': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)

            if otp_obj.otp == otp:
                otp_obj.delete()  # verified => delete to prevent reuse
                return Response({'message': 'OTP verified successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print("Error verifying OTP:", e)
            return Response({'error': 'Something went wrong'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class SetNewPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        phone = request.data.get('phone')
        print("SetNewPasswordView",phone,new_password,confirm_password)
        if not phone:
            return Response({'error': 'Session expired. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(phone=phone)
            user.password = make_password(new_password)
            user.save()

            # ✅ clear session after reset
            request.session.flush()

            return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class PasswordResetConfirmView(APIView):
    permission_classes =[permissions.AllowAny]
    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)

            if not default_token_generator.check_token(user, token):
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

            new_password = request.data.get('new_password')
            if not new_password:
                return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()

            return Response({'message': 'Password has been reset successfully'}, status=status.HTTP_200_OK)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(RetrieveAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class UpdateProfileView(UpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


# Product Views
class StandardResultsSetPagination(PageNumberPagination):
    permission_classes = [permissions.AllowAny]
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProductListView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        try:
            category_id = request.query_params.get('category_id', None)
            products = Product.objects.filter(is_active=True)
            
            if category_id:
                products = products.filter(category_id=category_id)
            
            paginator = StandardResultsSetPagination()
            result_page = paginator.paginate_queryset(products, request)
            serializer = ProductSerializer(result_page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)
        
        except Exception as e:
            print("💥 Error while fetching products:", str(e))
            return Response({'detail': 'Internal Server Error'}, status=500)


from django.db.models import Q

class ShopFilterListView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print('ShopFilterListView')
        """
        Filters products based on request body parameters:
        {
            "category_id": 1,
            "subcategory": "Mens",
            "color": "Black",
            "size": "M",
            "min_price": 250,
            "max_price": 500
        }
        """
        data = request.data
        print("data",data)
        category_id = data.get('category')
        subcategory = data.get('subcategory')   # Mens / Womens
        color = data.get('color')               # ex: Black
        size = data.get('size')                 # ex: M
        min_price = data.get('min_price')
        max_price = data.get('max_price')

        products = Product.objects.all()

        # 🔹 Category filter
        if category_id:
            products = products.filter(category_id=category_id)
            # print("category_id",products)
        # 🔹 Gender / subcategory filter
        if subcategory:
            products = products.filter(subcategory=subcategory)
            # print("subcategory",products)
        # 🔹 Color filter
        if color:
            products = products.filter(variants__variant_value__iexact=color)
            # print("color",products)
        # 🔹 Size filter (JSONField → contains lookup)
        if size:
            # Variant match filter (SQLite/MySQL)
            products = products.filter(
                variants__id__in=ProductVariant.objects.extra(
                    where=["JSON_EXTRACT(size, '$') LIKE %s"],
                    params=[f'%\"{size}\"%']
                ).values("id")
            )  
            # print("size",products)
            # # PostgreSQL supports `__contains`
            # products = products.filter(variants__size__contains=[size])


        # 🔹 Price filter
        if min_price and max_price:
            products = products.filter(
               
                Q(variants__price__gte=min_price, variants__price__lte=max_price)
            )
       
        elif min_price:
            products = products.filter(
                 Q(variants__price__gte=min_price)
            )

        elif max_price:
            products = products.filter(
                 Q(variants__price__lte=max_price)
            )

        # 🔹 remove duplicates
        products = products.distinct()
        # print("maibn products",products)
        # Pagination
        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)



class FilterListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        category = request.query_params.get('category', None)
        subcategory = request.query_params.get('subcategory', None)

        products = Product.objects.filter(is_active=True)

        if not category:  # covers both None and ""
            products = products.filter(subcategory=subcategory)
           
        else:
            products = products.filter(category__name=category,subcategory=subcategory)
        

        paginator = StandardResultsSetPagination()
        result_page = paginator.paginate_queryset(products, request)
        serializer = ProductSerializer(result_page, many=True)

        return paginator.get_paginated_response(serializer.data)




from django.db.models import Count, Q

class CategoryListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        categories = Category.objects.annotate(
            product_count=Count('product', filter=Q(product__is_active=True))
        ).filter(
            is_active=True,
            product_count__gt=0
        )

        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    # lookup_field = 'sku'



# Cart Views
class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """View Cart"""
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        """Add to Cart"""
        print(request.data)
        serializer = AddToCartSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            variant_id = serializer.validated_data.get('variant_id')   # color
            size_variant_id = serializer.validated_data.get('size_variant_id')  # size
            quantity = serializer.validated_data['quantity']

            try:
                product = Product.objects.get(id=product_id, is_active=True)
                cart, _ = Cart.objects.get_or_create(user=request.user)

                # validate variant
                variant = None
                if variant_id:
                    variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)

                # validate size_variant
                size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)

                cart_item_filter = {
                    'cart': cart,
                    'product': product,
                    'variant': variant,
                    'varient_size': size_variant,
                }

                cart_item, created = CartItem.objects.get_or_create(
                    **cart_item_filter,
                    defaults={'quantity': quantity},
                )

                if not created:
                    return Response({'message': 'Item already in cart..!'}, status=status.HTTP_200_OK)

                return Response({'message': 'Item added to cart'}, status=status.HTTP_201_CREATED)

            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
            except ProductVariant.DoesNotExist:
                return Response({'error': 'Product variant (color) not found'}, status=status.HTTP_404_NOT_FOUND)
            except SizeVariant.DoesNotExist:
                return Response({'error': 'Size variant not found'}, status=status.HTTP_404_NOT_FOUND)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, item_id):
        """Update Cart Item Quantity"""
        quantity = request.data.get('quantity')

        if item_id is None or quantity is None:
            return Response({'error': 'item_id and quantity are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)

            if int(quantity) <= 0:
                cart_item.delete()
                return Response({'message': 'Item removed from cart'}, status=status.HTTP_200_OK)

            cart_item.quantity = quantity
            cart_item.save()

            cart = cart_item.cart
            total = sum(
                (item.varient_size.get_price if item.varient_size else item.product.get_price) * item.quantity
                for item in cart.items.all()
            )

            return Response({
                'message': 'Cart updated successfully',
                'total': total
            })

        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, item_id):
        """Remove item from cart"""
        if not item_id:
            return Response({'error': 'item_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
            cart_item.delete()
            cart, _ = Cart.objects.get_or_create(user=request.user)
            serializer = CartSerializer(cart)

            return Response({'data': serializer.data, 'message': 'Item removed from cart'}, status=status.HTTP_200_OK)
        except CartItem.DoesNotExist:
            return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)



# Wishlist Views
@api_view(['GET'])
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    serializer = WishlistSerializer(wishlist_items, many=True)
    return Response(serializer.data)


class AddToWishlistSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=True)
    variant_id = serializers.IntegerField(required=True)
    variant_size = serializers.CharField(required=True)


from django.db import IntegrityError, transaction

class AddToWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddToWishlistSerializer(data=request.data)
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            variant_id = serializer.validated_data['variant_id']
            variant_size = serializer.validated_data['variant_size']

            try:
                product = Product.objects.get(id=product_id, is_active=True)
                try:
                    with transaction.atomic():
                        wishlist_item, created = Wishlist.objects.get_or_create(
                            user=request.user,
                            product=product,
                            variant_id=variant_id,
                            size_variant_id=variant_size
                        )
                except IntegrityError:
                    return Response({'message': 'Item already in wishlist'}, status=status.HTTP_200_OK)

                if created:
                    return Response({'message': 'Item added to wishlist'}, status=status.HTTP_201_CREATED)
                return Response({'message': 'Item already in wishlist'}, status=status.HTTP_200_OK)

            except Product.DoesNotExist:
                return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def remove_from_wishlist(request, product_id):
    try:
        wishlist_item = Wishlist.objects.get(user=request.user, product_id=product_id)
        wishlist_item.delete()
        return Response({'message': 'Item removed from wishlist'})
    except Wishlist.DoesNotExist:
        return Response({'error': 'Wishlist item not found'}, status=status.HTTP_404_NOT_FOUND)

# Order Views
class OrderApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(
            Q(user=request.user),
            Q(payment__status='Completed') | Q(payment__payment_method='Cash on Delivery')
        ).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)

        return Response(serializer.data)
    
        
    def post(self, request):
        user = request.user

        try:
            cart = Cart.objects.get(user=user)
            if cart.items.count() == 0:
                return Response({'message': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

            shipping_address = ShippingAddress.objects.filter(user=user, is_default=True).first()
            if not shipping_address:
                return Response({'message': 'Default shipping address not found.'}, status=status.HTTP_400_BAD_REQUEST)

            total_amount = cart.total_price

            order = Order.objects.create(
                user=user,
                total_amount=total_amount,
                shipping_address=shipping_address,
                billing_address=shipping_address.address_line1,
                phone=shipping_address.phone or user.phone,
                email=user.email,
            )

            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    size = item.varient_size,
                    quantity=item.quantity,
                    price=int(item.variant.price) * int(item.quantity) ,
                )

            cart.items.all().delete()  # Clear cart after order

            return Response({'message': 'Order created successfully', 'order_id': order.id})

        except Cart.DoesNotExist:
            return Response({'message': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)    

    def put(self, request, order_id):

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        print("Order Update Error:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Order.objects.filter()
    serializer_class = OrderSerializer

class PendingOrderApiView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        pending_orders = Order.objects.filter(user=request.user, status='pending').order_by('-created_at')
        serializer = OrderSerializer(pending_orders, many=True)

        return Response(serializer.data)


class BuyNowCheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        print("BuyNowCheckoutView",request.data)
        product_id = request.data.get("product_id")
        variant_id = request.data.get("variant_id")      # color
        size_variant_id = request.data.get("size_variant_id")  # ✅ size
        quantity = int(request.data.get("quantity", 1))

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response({"detail": "Product not found"}, status=400)

        # get color variant (optional)
        variant = None
        if variant_id:
            try:
                variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
            except ProductVariant.DoesNotExist:
                return Response({"detail": "Product variant not found"}, status=400)

        # get size variant (mandatory)
        try:
            size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)
        except SizeVariant.DoesNotExist:
            return Response({"detail": "Size variant not found"}, status=400)

        # effective price
        price = Decimal(size_variant.get_price)

        data = {
            "items": [
                {
                    "product": {
                        "id": product.id,
                        "name": product.name,
                    },
                    "variant": {
                        "id": variant.id if variant else None,
                        "color_name": variant.color_name if variant else None,
                        "hex_color_code": variant.hex_color_code if variant else None,
                        "images": variant.images.first().image.url if variant.images.first() else None,

                    } if variant else None,
                    "varient_size": {
                        "id": size_variant.id,
                        "size": size_variant.size,
                        "sku": size_variant.sku,
                        "price": float(size_variant.price),
                        "discount_price": float(size_variant.discount_price) if size_variant.discount_price else None,
                        "mrp": float(size_variant.mrp) if size_variant.mrp else None,
                        "get_price": float(size_variant.get_price),
                        "stock": size_variant.stock,
                    },
                    "quantity": quantity,
                    "subtotal": float(price * quantity),
                }
            ],
            "total_items": quantity,
            "total_price": float(price * quantity),
        }
        # print("checkout",data)
        return Response(data)




class CartCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response({"detail": "Cart is empty"}, status=404)

        serializer = CartCheckoutSerializer(cart)
        return Response(serializer.data)

import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# @api_view(['POST'])
# def create_order(request):
#     user = request.user  
#     if not user.is_authenticated:
#         return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

#     data = request.data
#     print("data",data)
#     order_type = data.get('type')  # 'cart' or 'buynow'

#     if order_type == 'cart':
#         try:
#             cart = Cart.objects.get(user=user)
#             if not cart.items.exists():
#                 return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

#             # Calculate total
#             total_amount = cart.total_price  # from CartSerializer / property

#             # Create Order
#             order = Order.objects.create(
#                 user=user,
#                 total_amount=total_amount,
#                 billing_address='',
#                 phone=user.phone or '',
#                 email=user.email,
#                 notes='',
#                 source=order_type
#             )

#             # Create OrderItems from CartItems
#             for cart_item in cart.items.all():
#                 OrderItem.objects.create(
#                     order=order,
#                     product=cart_item.product,
#                     variant=cart_item.variant,  # color
#                     size_variant=cart_item.varient_size,  # ✅ FK to SizeVariant
#                     quantity=cart_item.quantity,
#                     price=cart_item.varient_size.get_price if cart_item.varient_size else cart_item.product.get_price
#                 )

#             # Optional: clear cart after payment success

#         except Cart.DoesNotExist:
#             return Response({"error": "No cart found"}, status=status.HTTP_400_BAD_REQUEST)

#     elif order_type == 'buynow':
#         product_id = data.get('product_id')
#         variant_id = data.get('variant_id')          # color
#         size_variant_id = data.get('size_variant_id')  # ✅ size
#         quantity = int(data.get('quantity', 1))

#         if not (product_id and variant_id and size_variant_id):
      
#             return Response({"error": "Missing product/variant/size"}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             product = Product.objects.get(id=product_id, is_active=True)
#             variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
#             size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)

#             price = size_variant.get_price
#             total_amount = price * quantity

#             # Create Order
#             order = Order.objects.create(
#                 user=user,
#                 total_amount=total_amount,
#                 billing_address='',
#                 phone=user.phone or '',
#                 email=user.email,
#                 notes='',
#                 source=order_type
#             )

#             # Create single OrderItem
#             OrderItem.objects.create(
#                 order=order,
#                 product=product,
#                 variant=variant,           # color
#                 size_variant=size_variant, # ✅ size
#                 quantity=quantity,
#                 price=price
#             )

#         except (Product.DoesNotExist, ProductVariant.DoesNotExist, SizeVariant.DoesNotExist):
#             print("error Invalid product/var")
#             return Response({"error": "Invalid product/variant/size"}, status=status.HTTP_400_BAD_REQUEST)

#     else:
#         print("error: Invalid type")
#         return Response({"error": "Invalid type"}, status=status.HTTP_400_BAD_REQUEST)

#     # Razorpay Order creation
#     try:
#         payment_order = client.order.create({
#             "amount": int(order.total_amount * 100),  # in paise
#             "currency": "INR",
#             "payment_capture": "1",
#             "notes": {"order_id": order.order_number}
#         })

#         Payment.objects.create(
#             order=order,
#             payment_method='Razorpay',
#             amount=order.total_amount,
#             transaction_id=payment_order['id'],
#             gateway_response=payment_order
#         )

#         return Response({
#             "id": payment_order['id'],
#             "amount": payment_order['amount'],
#             "currency": payment_order['currency'],
#             "order_id": order.order_number
#         })

#     except razorpay.errors.BadRequestError as e:
#         print(e)
#         return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# def verify_payment(request):
#     data = request.data  # Razorpay response: razorpay_order_id, razorpay_payment_id, razorpay_signature
#     user = request.user
    
#     try:
#         # Verify signature (important for security)
#         client.utility.verify_payment_signature(data)
        
#         # Get your Order from notes or transaction_id
#         payment = Payment.objects.get(transaction_id=data['razorpay_order_id'])
#         order = payment.order
        
#         if order.user != user:
#             return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        
#         # Update Payment and Order
#         payment.status = 'Completed'
#         payment.payment_id = data.get('razorpay_payment_id') 
#         payment.gateway_response = data
#         payment.save()
        
#         order.status = 'Confirmed'
#         order.shipping_address_id = data.get('shipping_address_id')  # Send from frontend if needed
#         order.save()
        
#         for item in order.items.all():
#             size_variant = item.size_variant
#             if size_variant:
#                 if size_variant.stock >= item.quantity:
#                     size_variant.stock -= item.quantity
#                     size_variant.save()

#         # Clear cart only for cart orders
#         if order.source == 'cart' and Cart.objects.filter(user=user).exists():
#             Cart.objects.get(user=user).items.all().delete()  # Or delete the whole cart if preferred
        
#         return Response({"success": "Payment verified and order confirmed"})
    
#     except razorpay.errors.SignatureVerificationError:
#         return Response({"error": "Signature verification failed"}, status=status.HTTP_400_BAD_REQUEST)
#     except Payment.DoesNotExist:
#         return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)


# views.py
import json
from decimal import Decimal

from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions

import razorpay

from .models import Product, ProductVariant, SizeVariant, ShippingAddress, CustomUser

# init razorpay client (make sure RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET exist in settings)
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])  # keep only authenticated; if you want guest support, change this
def create_order(request):
    print("create_order",request.data)
    user = request.user
    if not user.is_authenticated:
        return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    data = request.data
    order_type = data.get('type')

    # calculate total_amount similarly to your initiate_payment
    if order_type == 'cart':
        try:
            cart = Cart.objects.get(user=user)
            if not cart.items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
            total_amount = cart.total_price
        except Cart.DoesNotExist:
            return Response({"error": "No cart found"}, status=status.HTTP_400_BAD_REQUEST)

    elif order_type == 'buynow':
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        size_variant_id = data.get('size_variant_id')
        quantity = int(data.get('quantity', 1))
        if not (product_id and variant_id and size_variant_id):
            return Response({"error": "Missing product/variant/size"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
            size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)
            # assuming size_variant.get_price returns Decimal or float
            price = Decimal(size_variant.get_price)
            total_amount = price * quantity
        except (Product.DoesNotExist, ProductVariant.DoesNotExist, SizeVariant.DoesNotExist):
            return Response({"error": "Invalid product/variant/size"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "Invalid type"}, status=status.HTTP_400_BAD_REQUEST)

    # optional: save shipping address if provided
    shipping_id = None
    shipping_data = data.get('shipping')
    if shipping_data:
        
        shipping_obj = ShippingAddress.objects.create(
            user=user,
            type_of_address=shipping_data.get('type_of_address', 'home'),
            state=shipping_data.get('state', ''),
            contact_person_name=shipping_data.get('contact_person_name'),
            contact_person_number=shipping_data.get('phone'),
            postal_code=shipping_data.get('postal_code'),
            address_line1=shipping_data.get('address_line1'),
            city=shipping_data.get('city'),
            country=shipping_data.get('country', 'India'),
            phone=shipping_data.get('phone'),
        )
        shipping_id = shipping_obj.id

    # create razorpay order (server-side)
    try:
        amount_paise = int((Decimal(total_amount) * 100).quantize(0))  # ensure integer paise
        notes = {
            "user_id": str(user.id),
            "type": order_type,
            "shipping_id": str(shipping_id) if shipping_id else "",
            "payload": json.dumps(data)
        }
        razorpay_order = client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": "1",
            "notes": notes
        })

        return Response({
            "key": settings.RAZORPAY_KEY_ID,
            "order_id": razorpay_order.get('id'),
            "amount": razorpay_order.get('amount'),
            "currency": razorpay_order.get('currency'),
            "shipping_id": shipping_id
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # catch Razorpay errors or Decimal conversion errors
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction
import json
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_payment(request):
    """
    Razorpay payment verification and order creation
    Steps:
    1. Verify payment signature
    2. Get customer data from Razorpay order
    3. Create/Get user and authenticate
    4. Create Order and ShippingAddress
    5. Update payment status
    """
    data = request.data
    
    try:
        # ✅ STEP 1: Verify Razorpay payment signature
        try:
            client.utility.verify_payment_signature({
                'razorpay_order_id': data.get('razorpay_order_id'),
                'razorpay_payment_id': data.get('razorpay_payment_id'),
                'razorpay_signature': data.get('razorpay_signature')
            })
        except Exception as e:
            logger.error(f"Payment signature verification failed: {str(e)}")
            return Response({
                "error": "Invalid payment signature",
                "message": "Payment verification failed. Illa signature match aagala."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # ✅ STEP 2: Fetch full payment details from Razorpay
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        
        try:
            razorpay_order = client.order.fetch(razorpay_order_id)
            logger.info(f"Razorpay Order Data: {razorpay_order}")
        except Exception as e:
            logger.error(f"Failed to fetch Razorpay order: {str(e)}")
            return Response({
                "error": "Failed to fetch order details",
                "message": "Razorpay la irundhu data get panna mudila."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ✅ STEP 2.1: Fetch Payment Details from Razorpay
        payment_details = {}
        try:
            if razorpay_payment_id:
                payment_details = client.payment.fetch(razorpay_payment_id)
                logger.info(f"Razorpay Payment Details: {payment_details}")
        except Exception as e:
            logger.warning(f"Failed to fetch payment details: {str(e)}")
        
        # ✅ STEP 3: Extract customer details from Razorpay response
        customer_details = razorpay_order.get('customer_details', {})
        
        raw_phone = customer_details.get('contact', '')
        customer_phone = raw_phone.replace('+91', '').replace('+', '').strip()
        customer_email = customer_details.get('email', '')
        
        shipping_data = customer_details.get('shipping_address', {})
        billing_data = customer_details.get('billing_address', {})
        address_data = shipping_data if shipping_data else billing_data
        customer_name = address_data.get('name', 'Customer')
        
        # ✅ STEP 4: Get order notes for product details
        notes = razorpay_order.get('notes', {})
        order_type = notes.get('type', 'cart')
        
        try:
            product_data = json.loads(notes.get('data', '{}'))
        except:
            product_data = {}
        
        # ✅ STEP 5: Create or Get User
        try:
            user = CustomUser.objects.filter(phone=customer_phone).first()

            if user:
                logger.info(f"Existing user found: {customer_phone}")
                is_new_user = False

            else:
                logger.info(f"Creating new user: {customer_phone}")

                # Always unique username
                base_username = customer_name.replace(" ", "").lower() if customer_name else f"user{customer_phone}"
                username = base_username

                # Ensure uniqueness
                counter = 1
                while CustomUser.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                user = CustomUser.objects.create_user(
                    username=username,
                    phone=customer_phone,
                    password=customer_phone,
                    email=customer_email if customer_email else None,
                    first_name=customer_name.split()[0] if customer_name else '',
                    last_name=' '.join(customer_name.split()[1:]) if len(customer_name.split()) > 1 else '',
                    user_type='customer'
                )
                is_new_user = True
                logger.info(f"New user created successfully: {customer_phone}")
        
        except Exception as e:
            logger.error(f"User creation/retrieval failed: {str(e)}")
            return Response({
                "error": "User creation failed",
                "message": f"User account can't create : {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ✅ STEP 6: Generate tokens for authentication
        try:
            token, _ = Token.objects.get_or_create(user=user)
        except Exception as e:
            logger.error(f"Token generation failed: {str(e)}")
            return Response({
                "error": "Authentication failed",
                "message": "Token generate panna mudila."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ✅ STEP 7: Create Order and Shipping Address in a transaction
        try:
            with transaction.atomic():
                # Create Shipping Address
                shipping_address = ShippingAddress.objects.create(
                    user=user,
                    contact_person_name=address_data.get('name', customer_name),
                    contact_person_number=address_data.get('contact', customer_phone).replace('+91', '').replace('+', ''),
                    address_line1=address_data.get('line1', ''),
                    address_line2=address_data.get('line2', ''),
                    city=address_data.get('city', ''),
                    state=address_data.get('state', ''),
                    country=address_data.get('country', 'IN'),
                    postal_code=address_data.get('zipcode', ''),
                    phone=address_data.get('contact', customer_phone).replace('+91', '').replace('+', ''),
                    type_of_address=address_data.get('tag', 'home').lower(),
                    landmark=address_data.get('landmark', ''),
                    is_default=True
                )
                logger.info(f"Shipping address created: {shipping_address.id}")
                
                # Create Order
                order = Order.objects.create(
                    user=user,
                    source=order_type,
                    total_amount=razorpay_order.get('amount', 0) / 100,
                    shipping_address=shipping_address,
                    billing_address=f"{billing_data.get('line1', '')}, {billing_data.get('line2', '')}, {billing_data.get('city', '')}, {billing_data.get('state', '')}, {billing_data.get('zipcode', '')}",
                    phone=customer_phone,
                    email=customer_email,
                    status='Confirmed'
                )
                logger.info(f"Order created: {order.order_number}")
                
                # ✅ STEP 8: Create Order Items based on order type
                if order_type == 'buynow':
                    product_id = product_data.get('product_id')
                    variant_id = product_data.get('variant_id')
                    size_variant_id = product_data.get('size_variant_id')
                    quantity = product_data.get('quantity', 1)
                    
                    if product_id and size_variant_id:
                        product = Product.objects.get(id=product_id)
                        size_variant = SizeVariant.objects.get(id=size_variant_id)
                        variant = ProductVariant.objects.get(id=variant_id) if variant_id else None
                        
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            variant=variant,
                            size_variant=size_variant,
                            quantity=quantity,
                            price=size_variant.get_price
                        )
                        
                        size_variant.stock -= quantity
                        size_variant.save()
                        logger.info(f"Order item created for Buy Now")
                
                elif order_type == 'cart':
                    cart = Cart.objects.filter(user=user).first()
                    if cart:
                        for cart_item in cart.items.all():
                            OrderItem.objects.create(
                                order=order,
                                product=cart_item.product,
                                variant=cart_item.variant,
                                size_variant=cart_item.varient_size,
                                quantity=cart_item.quantity,
                                price=cart_item.varient_size.get_price if cart_item.varient_size else cart_item.product.get_price
                            )
                            
                            if cart_item.varient_size:
                                cart_item.varient_size.stock -= cart_item.quantity
                                cart_item.varient_size.save()
                        
                        cart.items.all().delete()
                        logger.info(f"Cart items converted to order items and cart cleared")
                
                # ✅ STEP 9: Create/Update Payment record - FIXED LOGIC
                # Check payment method from payment_details
                payment_method_from_razorpay = payment_details.get('method', '')
                payment_status_from_razorpay = payment_details.get('status', '')
                
                # Determine if COD or Online Payment
                is_cod = payment_method_from_razorpay == 'cod'
                
                if is_cod:
                    # COD Order
                    cod_charge = 50.00  # ₹50 COD charge
                    order.total_amount = (order.total_amount or 0) + cod_charge
                    order.save()
                    payment_method_label = 'Cash on Delivery'
                    payment_status = 'Pending'
                    logger.info("COD order detected - Setting payment method as Cash on Delivery")
                else:
                    # Online Payment (wallet, card, upi, netbanking, etc.)
                    payment_method_label = 'Razorpay'
                    # Check if payment is captured/authorized
                    if payment_status_from_razorpay in ['captured', 'authorized']:
                        payment_status = 'Completed'
                    else:
                        payment_status = 'Pending'
                    logger.info(f"Online payment detected - Method: {payment_method_from_razorpay}, Status: {payment_status}")
                
                payment, created = Payment.objects.update_or_create(
                    order=order,
                    defaults={
                        'payment_method': payment_method_label,
                        'amount': order.total_amount,
                        'status': payment_status,
                        'transaction_id': razorpay_order_id,
                        'payment_id': razorpay_payment_id,
                        'signature_id': razorpay_signature,
                        'gateway_response': payment_details if payment_details else razorpay_order
                    }
                )
                logger.info(f"Payment record {'created' if created else 'updated'}: {payment.id} | Method: {payment_method_label} | Status: {payment_status}")
                        # ✅ STEP 11: Send Order Confirmation SMS via MSG91
                try:
                    # 1) Mobile prepare pannrom
                    mobile = str(customer_phone).strip()
                    if not mobile.startswith('91'):
                        if len(mobile) == 10 and mobile.isdigit():
                            mobile = '91' + mobile 
                        else:
                            logger.warning(f"Invalid mobile for SMS: {mobile}")
                            mobile = None

                    if mobile:
                        conn = http.client.HTTPSConnection("control.msg91.com")

                        payload = {
                            "flow_id": "6905efb8f9021a148f13ac92",  # ✅ Order confirmation template ID
                            "short_url": "1",
                            "sender": "MTEXTE",  
                            "recipients": [
                                {
                                    "mobiles": mobile,
                                    "name": customer_name,
                                    "id": str(order.order_number),
                                }
                            ]
                        }

                        headers = {
                            "accept": "application/json",
                            "authkey": "470722Ae1mHUuQ3W6902fc0fP1",  
                            "content-type": "application/json"
                        }

                        logger.info(f"Sending order confirmation SMS to {mobile} for order {order.order_number}")
                        conn.request("POST", "/api/v5/flow", json.dumps(payload), headers)
                        res = conn.getresponse()
                        body = res.read().decode()
                        logger.info(f"MSG91 Order SMS response: {body}")

                        try:
                            sms_resp = json.loads(body)
                            if sms_resp.get("type") == "success":
                                logger.info("✅ Order confirmation SMS sent successfully")
                            else:
                                logger.warning(f"⚠️ Order SMS failed: {sms_resp}")
                        except Exception:
                            logger.warning("⚠️ Failed to parse MSG91 SMS response")

                except Exception as sms_e:
                    logger.warning(f"⚠️ Order confirmation SMS sending failed: {sms_e}")

        
        except Exception as e:
            logger.error(f"Order creation failed: {str(e)}")
            return Response({
                "error": "Order creation failed",
                "message": f"Order create panna mudila: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # ✅ STEP 10: Success Response
        return Response({
            "success": True,
            "message": "Payment verified and order created successfully!",
            "user": {
                "id": user.id,
                "phone": user.phone,
                "email": user.email,
                "username": user.get_full_name(),
                "first_name": user.get_full_name(),
            },
            "order": {
                "order_number": order.order_number,
                "order_id": order.id,
                "total_amount": float(order.total_amount),
                "status": order.status
            },
            "payment": {
                "method": payment_method_label,
                "status": payment_status
            },
            'token': token.key,
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"Unexpected error in payment verification: {str(e)}")
        return Response({
            "error": "Payment verification failed",
            "message": f"Unexpected error: {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# views.py
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def create_razorpay_order(request):
    data = {
        "amount": request.data['amount'],
        "currency": "INR",
        "receipt": request.data['receipt'],
        "notes": request.data.get('notes', {})
    }
    order = client.order.create(data=data)
    return Response({"order_id": order['id']})



import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

DELHIVERY_PINCODE_URL = "https://track.delhivery.com/c/api/pin-codes/json/"

def check_delhivery_serviceability(pincode: str) -> bool:
    """
    Delhivery LIVE Pincode Serviceability check.
    Returns True if pincode is serviceable, False otherwise.
    """
    try:
        headers = {
            "Authorization": f"Token {settings.DELHIVERY_API_TOKEN}"
        }
        params = {
            "filter_codes": pincode
        }

        response = requests.get(
            DELHIVERY_PINCODE_URL,
            headers=headers,
            params=params,
            timeout=5.0
        )
        response.raise_for_status()  # Raise exception for 4xx/5xx status codes

        data = response.json()
        delivery_codes = data.get("delivery_codes", [])

        if not delivery_codes:
            logger.warning(f"No delivery codes found for pincode: {pincode}")
            return False

        postal_code = delivery_codes[0].get("postal_code", {})
        remarks = (postal_code.get("remarks") or "").strip()

        if remarks.lower() == "embargo":
            logger.info(f"Pincode {pincode} is under embargo")
            return False

        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Delhivery request error for pincode {pincode}: {e}")
        return False
    except Exception as e:
        logger.error(f"Delhivery unexpected error for pincode {pincode}: {e}", exc_info=True)
        return False

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def shipping_info(request):
    """
    Razorpay Magic Checkout Shipping Info API
    Returns shipping serviceability, COD serviceability, shipping fees and COD fees
    """
    logger.info(f"shipping_info request: {request.data}")
    
    try:
        data = request.data
        
        # Extract request parameters
        order_id = data.get('order_id')
        razorpay_order_id = data.get('razorpay_order_id')
        email = data.get('email')
        contact = data.get('contact')
        addresses = data.get('addresses', [])
        
       
        response_addresses = []
        
        for address in addresses:
            address_id = address.get('id')
            zipcode = address.get('zipcode')
            state_code = address.get('state_code', '')
            country = address.get('country')
            
            # Validate address fields
            if not all([address_id, zipcode, country]):
                continue
            
             # 🔍 Step 1: Delhivery la pincode serviceability check
            try:
                is_serviceable = check_delhivery_serviceability(str(zipcode))
                
            except Exception as check_error:
                logger.error(f"Error checking serviceability: {check_error}", exc_info=True)
                is_serviceable = False

            # Define shipping methods
            # You can customize this based on your business logic
            shipping_methods = [
                {
                    "id": "1",
                    "description": "Free shipping with COD available",
                    "name": "Standard Delivery (5-7 days)",
                    "serviceable": is_serviceable,
                    "shipping_fee": 0,  # Free shipping (0 paise)
                    "cod": True if is_serviceable else False,  # COD enabled
                    "cod_fee": 5000 if is_serviceable else 0  # ₹50 COD fee (5000 paise)
                },
                
            ]
            
            # Build response for this address
            response_addresses.append({
                "id": address_id,
                "zipcode": zipcode,
                "state_code": state_code,
                "country": country,
                "shipping_methods": shipping_methods
            })
        
        # Return response in Razorpay format
        print(response_addresses)

        return Response({
            "addresses": response_addresses
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(f"Shipping info error: {str(e)}")
        return Response(
            {"error": "Failed to process shipping info"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def initiate_payment(request):
    print("initiate_payment",request.data)
    user = request.user  
    # if not user.is_authenticated:
    #     return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    data = request.data
    order_type = data.get('type')  # 'cart' or 'buynow'

    if order_type == 'cart':
        try:
            cart = Cart.objects.get(user=user)
            if not cart.items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

            total_amount = cart.total_price

        except Cart.DoesNotExist:
            return Response({"error": "No cart found"}, status=status.HTTP_400_BAD_REQUEST)

    elif order_type == 'buynow':
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        size_variant_id = data.get('size_variant_id')
        quantity = int(data.get('quantity', 1))

        if not (product_id and variant_id and size_variant_id):
            return Response({"error": "Missing product/variant/size"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, is_active=True)
            variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
            size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)

            price = size_variant.get_price
            total_amount = price * quantity

        except (Product.DoesNotExist, ProductVariant.DoesNotExist, SizeVariant.DoesNotExist):
            return Response({"error": "Invalid product/variant/size"}, status=status.HTTP_400_BAD_REQUEST)

    else:
        return Response({"error": "Invalid type"}, status=status.HTTP_400_BAD_REQUEST)

    # Razorpay order creation
    try:
        razorpay_order = client.order.create({
            "amount": int(total_amount * 100),  # in paise
            "currency": "INR",
            "payment_capture": "1",
            "notes": {
                "user_id": str(user.id),
                "type": order_type,
                "data": json.dumps(data)
            }
        })

        # Return to frontend
        return Response({
            "razorpay_order_id": razorpay_order['id'],
            "amount": razorpay_order['amount'],
            "currency": razorpay_order['currency']
        })

    except razorpay.errors.BadRequestError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
def confirm_order(request):
    user = request.user
    data = request.data
    if not user.is_authenticated:
        return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        # 1. Verify Razorpay signature
        client.utility.verify_payment_signature(data)

        # 2. Get extra data from Razorpay notes
        razorpay_order_id = data.get("razorpay_order_id")
        payment_id = data.get("razorpay_payment_id")
        order_type = data.get("type")
        notes_data = json.loads(data.get("notes_data", "{}"))
        shipping_address_id = data.get("shipping_address_id")

        # ✅ Get the address object
        shipping_address = get_object_or_404(ShippingAddress, id=shipping_address_id)
        print("shipping_address",shipping_address)

        if order_type == 'cart':
            cart = Cart.objects.get(user=user)
            if not cart.items.exists():
                return Response({"error": "Cart empty"}, status=status.HTTP_400_BAD_REQUEST)

            total_amount = cart.total_price

        elif order_type == 'buynow':
            product_id = data.get('product_id') or notes_data.get("product_id")
            variant_id = data.get('variant_id') or notes_data.get("variant_id")
            size_variant_id = data.get('size_variant_id') or notes_data.get("size_variant_id")
            quantity = int(data.get('quantity', 1)) or int(notes_data.get("quantity", 1))

            product = Product.objects.get(id=product_id, is_active=True)
            variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
            size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)
            total_amount = size_variant.get_price * quantity

        else:
            return Response({"error": "Invalid order type"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Create Order
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            billing_address=shipping_address.address_line1,
            shipping_address=shipping_address, 
            phone=user.phone or '',
            email = user.email or f"{user.phone}@gmail.com",
            notes='',
            source=order_type,
            status='Confirmed'
        )

        if order_type == 'cart':
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    size_variant=item.varient_size,
                    quantity=item.quantity,
                    price=item.varient_size.get_price if item.varient_size else item.product.get_price
                )
        else:
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                size_variant=size_variant,
                quantity=quantity,
                price=size_variant.get_price
            )

        # 4. Create Payment record
        Payment.objects.create(
            order=order,
            payment_method='Razorpay',
            amount=total_amount,
            transaction_id=razorpay_order_id,
            payment_id=payment_id,
            status='Completed',
            gateway_response=data
        )

        # after Payment.objects.create(...)
        try:
            
            authkey = settings.MSG91_API_KEY        # or settings.MSG91_AUTHKEY
            template_id = settings.MSG91_TEMPLATE_ORDER_CONFIRMED      # or settings.MSG91_TEMPLATE_ORDER_CONFIRM

            user_mobile = user.phone
            user_name = user.first_name or user.username
            order_id = str(order.order_number)

            sms_result = send_order_sms(authkey, template_id, user_mobile, user_name, order_id)

            if not sms_result["success"]:
                logger.warning(f"SMS not sent for order {order_id}: {sms_result['detail']}")
            else:
                logger.info(f"SMS sent successfully to {user_mobile}")

        except Exception as e:
            logger.exception(f"Non-fatal SMS send error: {str(e)}")



        # 5. Update stock
        for item in order.items.all():
            if item.size_variant and item.size_variant.stock >= item.quantity:
                item.size_variant.stock -= item.quantity
                item.size_variant.save()

        # 6. Clear cart (if cart)
        if order_type == 'cart':
            cart.items.all().delete()

        return Response({"success": "Order placed successfully", "order_id": order.order_number})

    except razorpay.errors.SignatureVerificationError:
        return Response({"error": "Signature verification failed"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
def cod_order_create(request):
    user = request.user

    if not user.is_authenticated:
        return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)

    data = request.data
    order_type = data.get('type')  # 'cart' or 'buynow'
    shipping_address_id = data.get('shipping_address_id')

    if not shipping_address_id:
        return Response({"error": "Shipping address required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        shipping_address = ShippingAddress.objects.get(id=shipping_address_id, user=user)
    except ShippingAddress.DoesNotExist:
        return Response({"error": "Invalid shipping address"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        if order_type == 'cart':
            cart = Cart.objects.get(user=user)
            if not cart.items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

            total_amount = cart.total_price

        elif order_type == 'buynow':
            product_id = data.get('product_id')
            variant_id = data.get('variant_id')
            size_variant_id = data.get('size_variant_id')
            quantity = int(data.get('quantity', 1))

            if not (product_id and variant_id and size_variant_id):
                return Response({"error": "Missing product/variant/size"}, status=status.HTTP_400_BAD_REQUEST)

            product = Product.objects.get(id=product_id, is_active=True)
            variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
            size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)

            total_amount = size_variant.get_price * quantity

        else:
            return Response({"error": "Invalid order type"}, status=status.HTTP_400_BAD_REQUEST)

        # COD charges (like ₹50)
        cod_fee = 50
        final_amount = total_amount + cod_fee

        # ✅ Create Order
        order = Order.objects.create(
            user=user,
            total_amount=final_amount,
            billing_address=shipping_address.address_line1,
            shipping_address=shipping_address,
            phone=user.phone or '',
            email=user.email,
            notes='Cash on Delivery order',
            source=order_type,
            status='Pending'  # COD orders start as pending
        )

        # ✅ Create Order Items
        if order_type == 'cart':
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    variant=item.variant,
                    size_variant=item.varient_size,
                    quantity=item.quantity,
                    price=item.varient_size.get_price if item.varient_size else item.product.get_price
                )
        else:
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                size_variant=size_variant,
                quantity=quantity,
                price=size_variant.get_price
            )

        # ✅ Create Payment record (COD)
        Payment.objects.create(
            order=order,
            payment_method='Cash on Delivery',
            amount=final_amount,
            transaction_id='COD-' + str(order.order_number),
            status='Pending',
            gateway_response={}
        )

        # after Payment.objects.create(...)
        try:
            
            authkey = settings.MSG91_API_KEY        # or settings.MSG91_AUTHKEY
            template_id = settings.MSG91_TEMPLATE_ORDER_CONFIRMED      # or settings.MSG91_TEMPLATE_ORDER_CONFIRM

           
            user_mobile = user.phone
            user_name = user.get_full_name() or user.username
            order_id = str(order.order_number)

            sms_result = send_order_sms(authkey, template_id, user_mobile, user_name, order_id)

            if not sms_result["success"]:
                logger.warning(f"SMS not sent for order {order_id}: {sms_result['detail']}")
            else:
                logger.info(f"SMS sent successfully to {user_mobile}")

        except Exception as e:
            logger.exception(f"Non-fatal SMS send error: {str(e)}")


        # ✅ Reduce stock
        for item in order.items.all():
            if item.size_variant and item.size_variant.stock >= item.quantity:
                item.size_variant.stock -= item.quantity
                item.size_variant.save()

        # ✅ Clear cart if needed
        if order_type == 'cart':
            cart.items.all().delete()

        # ✅ Generate shipment label
        # create_shipping_label(request, order_id=order.id)

        return Response({
            "success": "COD order placed successfully",
            "order_id": order.order_number,
            "total": final_amount,
            "cod_fee": cod_fee
        })

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

from decimal import Decimal

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def magic_checkout_initiate_payment(request):
    print("initiate_payment", request.data)
    user = request.user
    data = request.data
    order_type = data.get('type')  # 'cart' or 'buynow'

    line_items = []
    total_amount = 0

    # -----------------------------------------------------------
    # CASE 1 : CART CHECKOUT
    # -----------------------------------------------------------
    if order_type == 'cart':
        try:
            cart = Cart.objects.get(user=user)
            if not cart.items.exists():
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

            for item in cart.items.all():
                product = item.product
                variant = item.variant
                size_variant = item.varient_size

                price = size_variant.get_price
                quantity = item.quantity
                total_amount += price * quantity

                # 🔥 GET DEFAULT IMAGE FROM ProductVariantImage
                default_image = variant.images.filter(is_default=True).first()

                image_url = ""
                if default_image:
                    # request.build_absolute_uri() use get full URL 
                    image_url = request.build_absolute_uri(default_image.image.url)

                line_items.append({
                    "sku": str(product.sku or ""),
                    "variant_id": str(variant.id),
                    "other_product_codes": {
                        "upc":  "",
                        "ean":  "",
                        "unspsc":  "",
                    },
                    "price": int(price * 100),
                    "offer_price": int(price * 100),
                    "tax_amount": 0,
                    "quantity": int(quantity),
                    "name": product.name,
                    "description": (product.description or "")[:20],
                    "weight":  0,
                    "dimensions": {
                        "length":  0,
                        "width":  0,
                        "height":  0,
                    },
                    "image_url":  image_url,
                    "product_url": request.build_absolute_uri(f"https://mtex.in/product/{product.id}/"),
                    "notes": {}
                })

        except Cart.DoesNotExist:
            return Response({"error": "No cart found"}, status=status.HTTP_400_BAD_REQUEST)


    # -----------------------------------------------------------
    # CASE 2 : BUY NOW CHECKOUT
    # -----------------------------------------------------------
    elif order_type == 'buynow':
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        size_variant_id = data.get('size_variant_id')
        quantity = int(data.get('quantity', 1))

        if not (product_id and variant_id and size_variant_id):
            return Response({"error": "Missing product/variant/size"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id, is_active=True)
            variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
            size_variant = SizeVariant.objects.get(id=size_variant_id, variant=variant)

            price = float(size_variant.get_price)
            total_amount = price * quantity

            # 🔥 GET DEFAULT IMAGE FROM ProductVariantImage
            default_image = variant.images.filter(is_default=True).first()

            image_url = ""
            if default_image:
                # request.build_absolute_uri() use get full URL 
                image_url = request.build_absolute_uri(default_image.image.url)

            line_items.append({
                "sku": str(product.sku or ""),
                "variant_id": str(variant.id),
                "other_product_codes": {
                    "upc": "",
                    "ean": "",
                    "unspsc": "",
                },
                "price": int(price * 100),
                "offer_price": int(price * 100),
                "tax_amount": 0,
                "quantity": quantity,
                "name": product.name,
                "description": (product.description or "")[:20],
                "weight":  0,
                "dimensions": {
                    "length":  0,
                    "width": 0,
                    "height":  0,
                },
                "image_url":  image_url,
                "product_url": f'https://mtex.in/product/{product.id}',
                "notes": {}
            })

        except (Product.DoesNotExist, ProductVariant.DoesNotExist, SizeVariant.DoesNotExist):
            return Response({"error": "Invalid product/variant/size"}, status=status.HTTP_400_BAD_REQUEST)

    else:
        return Response({"error": "Invalid type"}, status=status.HTTP_400_BAD_REQUEST)


    # -----------------------------------------------------------
    # CREATE RAZORPAY ORDER WITH MAGIC CHECKOUT FORMAT
    # -----------------------------------------------------------
    try:
        
        payload = {
            "amount": int(total_amount * 100),  # Must be integer in paise
            "currency": "INR",
            "receipt": f"rcpt_{timezone.now().strftime('%Y%m%d%H%M%S')}",
            "notes": {
                "user_id": str(user.id),
                "type": order_type,
                "data": json.dumps(data)
            },
            "line_items_total": int(total_amount * 100),  # Must be integer in paise
            "line_items": line_items,
        }

        razorpay_order = client.order.create(payload)
        return Response({
            "razorpay_order_id": razorpay_order['id'],
            "amount": razorpay_order['amount'],
            "currency": razorpay_order['currency'],
            "line_items": line_items
        })

    except razorpay.errors.BadRequestError as e:
        print("Razorpay Error:", str(e))
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


import json
import hmac
import hashlib
from django.conf import settings
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from django.db import transaction

from .models import OrderTracking, TrackingScan
from api.models import Order  # adjust import path if Order is elsewhere

@csrf_exempt
def delhivery_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    # 1) Verify signature (if you set DELHIVERY_WEBHOOK_SECRET)
    secret = getattr(settings, "DELHIVERY_WEBHOOK_SECRET", None)
    if secret:
        # Delhivery might send signature header name differently; try common headers
        signature = request.headers.get("X-DELHIVERY-SIGNATURE") or request.headers.get("X-SIGNATURE") or request.headers.get("X-Hub-Signature")
        if not signature:
            return HttpResponse(status=403)
        computed = hmac.new(secret.encode(), msg=request.body, digestmod=hashlib.sha256).hexdigest()
        if not hmac.compare_digest(computed, signature):
            return HttpResponse(status=403)

    # 2) Parse JSON body
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    # 3) Extract AWB / event id / shipment info (try a few common shapes)
    awb = payload.get("waybill") or payload.get("awb") or payload.get("waybill_number")
    if not awb:
        # nested style: {"ShipmentData":[{"Shipment":{...}}]}
        try:
            awb = payload.get("ShipmentData", [{}])[0].get("Shipment", {}).get("Waybill")
        except Exception:
            awb = None

    if not awb:
        return HttpResponseBadRequest("AWB not found in payload")

    event_id = payload.get("event_id") or payload.get("id") or payload.get("ShipmentData", [{}])[0].get("EventID")

    # 4) Load tracking row
    try:
        tracking = OrderTracking.objects.get(awb_number=awb)
    except OrderTracking.DoesNotExist:
        # optionally create it or log and return 200 so Delhivery won't retry too aggressively
        return JsonResponse({"status": "tracking_not_found"}, status=200)

    # 5) Idempotency: ignore duplicate event
    if event_id and tracking.last_event_id == event_id:
        return JsonResponse({"status": "duplicate_event"}, status=200)

    # 6) Extract status and scans (generic)
    status = None
    scans_list = []
    if "ShipmentData" in payload:
        shipment = payload["ShipmentData"][0].get("Shipment", {})
        status = shipment.get("Status")
        raw_scans = shipment.get("Scans", [])
        for s in raw_scans:
            scan = s.get("Scan") if isinstance(s, dict) else s
            scans_list.append({
                "status": scan.get("Status"),
                "location": scan.get("Location"),
                "time": scan.get("Time") or scan.get("scan_time")
            })
    else:
        status = payload.get("status") or payload.get("current_status")
        raw_scans = payload.get("scans") or []
        for scan in raw_scans:
            scans_list.append({
                "status": scan.get("status") or scan.get("Status"),
                "location": scan.get("location") or scan.get("Location"),
                "time": scan.get("time") or scan.get("Time")
            })

    # 7) Persist changes inside transaction
    with transaction.atomic():
        tracking.raw_data = payload
        if status:
            tracking.current_status = status
        if event_id:
            tracking.last_event_id = event_id
        tracking.save()

        # Create scans if new (simple de-dup by scan_time + status)
        existing = set(tracking.scans.values_list("scan_time", "status"))
        for s in scans_list:
            scan_time = None
            try:
                scan_time = parse_datetime(s.get("time")) if s.get("time") else None
                if scan_time and timezone.is_naive(scan_time):
                    scan_time = timezone.make_aware(scan_time)
            except Exception:
                scan_time = None

            key = (scan_time, s.get("status"))
            if key in existing:
                continue

            TrackingScan.objects.create(
                tracking=tracking,
                status=s.get("status") or "unknown",
                location=s.get("location"),
                scan_time=scan_time or timezone.now(),
            )

        # 8) Update Order.status mapping (tweak mapping to your terms)
        order = tracking.order
        status_lower = (tracking.current_status or "").lower()
        if "deliv" in status_lower:  # delivered/delivery
            order.status = "Delivered"
        elif "out for delivery" in status_lower or "out_for_delivery" in status_lower:
            order.status = "Shipped"
        elif "transit" in status_lower or "in transit" in status_lower:
            order.status = "Shipped"
        elif "cancel" in status_lower or "returned" in status_lower:
            order.status = "Cancelled"
        order.save()

        # optional: notify user (email/push) if status changed to important states

    return JsonResponse({"status": "ok"}, status=200)





class ShippingAddressListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        addresses = ShippingAddress.objects.filter(user=request.user)
        serializer = ShippingAddressSerializer(addresses, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ShippingAddressSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShippingAddressDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return ShippingAddress.objects.get(pk=pk, user=user)
        except ShippingAddress.DoesNotExist:
            return None

    def put(self, request, pk):
        address = self.get_object(pk, request.user)
        if not address:
            return Response({"detail": "Address not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ShippingAddressSerializer(address, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        print("error",serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        address = self.get_object(pk, request.user)
        if not address:
            return Response({"detail": "Address not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ShippingAddressSerializer(address, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        address = self.get_object(pk, request.user)
        if not address:
            return Response({"detail": "Address not found."}, status=status.HTTP_404_NOT_FOUND)
        address.delete()
        return Response({"detail": "Address deleted."}, status=status.HTTP_204_NO_CONTENT)


class ReturnRequestCreateView(APIView):
    def post(self, request):
        print("create_return_request",request.data)
        order_item_id = request.data.get('item_id')
        request_type = request.data.get('request_type')  # 'Return' or 'Exchange'

        try:
            order_item = OrderItem.objects.get(id=order_item_id, order__user=request.user)
        except OrderItem.DoesNotExist:
            return Response({"error": "Invalid order item."}, status=status.HTTP_400_BAD_REQUEST)

        # ❗ Check if a return/exchange request already exists for this item
        existing_request = ReturnRequest.objects.filter(
            order_item=order_item,
            user=request.user,
            status__in=[
                'Requested', 'Approved', 'Received', 'Inspected', 'Refunded', 'Exchanged'
            ]
        ).first()

        if existing_request:
            return Response({
                "error": f"A {existing_request.request_type.lower()} request is already active for this item."
            }, status=status.HTTP_400_BAD_REQUEST)


        delivery_date = order_item.order.delivery_date
        product = order_item.product

        if not delivery_date:
            return Response({"error": "Delivery date not available."}, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.now().date()
        delivered_on = delivery_date.date()

        days_since_delivery = (today - delivered_on).days

        # Type-based period check
        if request_type == 'Return':
            if not product.is_returnable:
                return Response({"error": "This product is not returnable."}, status=status.HTTP_400_BAD_REQUEST)
            if days_since_delivery > product.return_period:
                return Response({"error": "Return period expired."}, status=status.HTTP_400_BAD_REQUEST)

        elif request_type == 'Exchange':
            if not product.is_replaceable:
                return Response({"error": "This product is not replaceable."}, status=status.HTTP_400_BAD_REQUEST)
            if days_since_delivery > product.replace_period:
                return Response({"error": "Replacement period expired."}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"error": "Invalid request type."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Passed all checks, create return/exchange request
        return_request = ReturnRequest.objects.create(
            order_item=order_item,
            user=request.user,
            request_type=request_type,
            quantity=request.data.get('quantity', 1),
            reason=request.data.get('reason', ''),
            images=request.data.get('images', None)
        )

        return Response({"message": f"{request_type} request submitted successfully."}, status=status.HTTP_201_CREATED)
