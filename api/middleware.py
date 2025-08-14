from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import json
import logging
logger = logging.getLogger(__name__)


class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        def __call__(self, request):
            print("Processing request: {request.method} {request.path}")
            logger.debug(f"Processing request: {request.method} {request.path}")
        # Skip JWT validation for certain paths
        skip_paths = [
            '/api/login/',
            '/api/register/',
            '/api/refresh/',
            '/admin/',
            '/dashboard/',
        ]
        # Skip JWT validation for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return self.get_response(request)
        
        # Check if the request path should skip JWT validation
        if any(request.path.startswith(path) for path in skip_paths):
            response = self.get_response(request)
            return response
        
        # Only apply JWT authentication to API endpoints
        if request.path.startswith('/api/'):
            jwt_auth = JWTAuthentication()
            try:
                # Try to authenticate the request
                auth_result = jwt_auth.authenticate(request)
                if auth_result:
                    request.user, request.auth = auth_result
            except (InvalidToken, TokenError) as e:
                # Return JSON error response for invalid tokens
                return JsonResponse({
                    'error': 'Invalid or expired token',
                    'detail': str(e)
                }, status=401)
        
        response = self.get_response(request)
        return response