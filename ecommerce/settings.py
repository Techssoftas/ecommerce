import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ["m2hit.in", "www.m2hit.in",'13.204.192.59','*' ,"127.0.0.1", "localhost"]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_crontab',
    'dashboard.apps.DashboardConfig',
    # Third party apps
   
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'crispy_forms',
    'crispy_bootstrap5',
    
    # Local apps
    # 'dashboard',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # top
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# SESSION_COOKIE_NAME = 'sessionid'
# SESSION_COOKIE_SECURE = False   # set to True only in HTTPS
# CSRF_COOKIE_SECURE = False
# SESSION_COOKIE_SAMESITE = 'None'  # important when using withCredentials and different domain


CRONJOBS = [
    ('0 0 * * *', 'api.cron.delete_expired_otps'),  # every day at midnight
]


ROOT_URLCONF = 'ecommerce.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ecommerce.wsgi.application'

# Database
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mtexdb',
        'USER': 'admin',
        'PASSWORD': 'L3g7#R83s$X#',
        'HOST': 'mtexdb.c1coqyua89pn.ap-south-1.rds.amazonaws.com',
        'PORT': '3306',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),  # Adjust to your static folder path
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Where static files are collected for production

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'api.CustomUser'
DOMAIN = "https://m2hit.in"

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
      'rest_framework.authentication.TokenAuthentication', 
        # 'rest_framework_simplejwt.authentication.JWTAuthentication',
        # 'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# JWT Configuration
from datetime import timedelta


# CORS Configuration
# CORS_ALLOW_ALL_ORIGINS = True  

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://192.168.29.20:5173",#yogavarthini
    'http://192.168.29.150:5173',#my
    'http://192.168.29.3:5173',#naveen
    'https://santhiya.d2k2gry4kzssr.amplifyapp.com',
    "https://m2hit.in",
    "https://www.m2hit.in",
    "https://mtex.in", 
    "https://www.mtex.in", 
    "https://mtex-ecommerce.surge.sh"
]

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://m2hit.in",
    "https://www.m2hit.in",
    "https://www.mtex.in",
    "https://mtex.in",  
    "https://mtex-ecommerce.surge.sh",
]


CORS_ALLOW_CREDENTIALS = True  # 



CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'ngrok-skip-browser-warning'
]


# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Login URLs
LOGIN_URL = '/login_view/'
LOGIN_REDIRECT_URL = '/dashboard/'


DATA_UPLOAD_MAX_MEMORY_SIZE = 209715200   # 200 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 209715200   # 200 MB



import logging

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # keeps the default Django loggers
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',  # Or INFO in production
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'django_app.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        # Logger for your app/module
        'dashboard': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}






#Live Key
RAZORPAY_KEY_ID = "rzp_live_RFnXxVu9Ihl4Rv"
RAZORPAY_KEY_SECRET = "9hcZNAZmxQOURfKTXUGYKCuG"

# # #Test Key
# RAZORPAY_KEY_ID = "rzp_test_RCJ4LxmMOSnvyB"
# RAZORPAY_KEY_SECRET = "eB8kvT0n5XI2fQyk9QrmVPJu"


DELHIVERY_API_TOKEN = "d7c1fdb1b8ca98d9fd3fc884a771fd4e96ffaf1e"

# settings.py (example)
DELHIVERY_PROD_URL = "https://track.delhivery.com/api/cmu/create.json"
DELHIVERY_STAGING_URL = "https://staging-express.delhivery.com/api/cmu/create.json"
DELHIVERY_TOKEN = "d7c1fdb1b8ca98d9fd3fc884a771fd4e96ffaf1e"     # get from Delhivery portal
DELHIVERY_PICKUP_LOCATION = "2/227 D, ANGALAPARMESHWARI NAGAR, Mudalipalayam, Tiruppur, 641606"  # case-sensitive
DELHIVERY_SELLER_GST_TIN = "33FLMPM1010A1ZY"   # if you pass GST from API
DELHIVERY_CLIENT_GST_TIN = "M TEX"
DELHIVERY_COMPANY_NAME = "M TEX"
DELHIVERY_BASE_URL ="https://track.delhivery.com/api/cmu/create.json" #production url
# DELHIVERY_BASE_URL ="https://staging-express.delhivery.com/api/cmu/create.json" #testing url



#Email Settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtpout.secureserver.net'  # GoDaddy SMTP
EMAIL_PORT = 587  # For SSL
EMAIL_HOST_USER = 'fashion@mtex.in'       # Ex: noreply@mtex.in
EMAIL_HOST_PASSWORD = 'L3g7#R83s$X#'  # App password if enabled
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


#SMS Settings

MSG91_API_KEY = "470722Ae1mHUuQ3W6902fc0fP1"  # auth key
MSG91_SENDER_ID = "MTEXTE"            # BSNL header name
MSG91_ROUTE = "4"                     # transactional route
MSG91_REG_TEMPLATE_ID = "69059476c859393d1f62a803"  # BSNL DLT template ID for registration
MSG91_TEMPLATE_ORDER_CONFIRMED = "6905efb8f9021a148f13ac92" 


