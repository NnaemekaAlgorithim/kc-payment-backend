#!/bin/bash

# Django Project Generator Script
# Usage: ./start_django.sh <project_name>
# Example: ./start_django.sh inventory

set -e

# Function to run Django management commands with proper environment
run_django_command() {
    export DEBUG=True
    export DJANGO_SETTINGS_MODULE="${PROJECT_NAME}.${PROJECT_NAME}.settings.dev_settings"
    # Ensure the .env file is created before running commands
    if [ ! -f ".env" ]; then
        echo "DEBUG=True" > ".env"
    fi
    # Ensure we have the python-decouple package
    python -c "import decouple" 2>/dev/null || pip install python-decouple
    "$@"
}

# Check if project name is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a project name"
    echo "Usage: $0 <project_name>"
    echo "Example: $0 inventory"
    exit 1
fi

PROJECT_NAME=$1
BASE_DIR=$(pwd)
PROJECT_DIR="$BASE_DIR/$PROJECT_NAME"

# Check if project already exists
if [ -d "$PROJECT_NAME" ] || [ -f "manage.py" ] || [ -f "requirements.txt" ]; then
    echo "Warning: A Django project or related files already exist in this directory."
    echo "Found:"
    [ -d "$PROJECT_NAME" ] && echo "  - Project directory: $PROJECT_NAME/"
    [ -f "manage.py" ] && echo "  - manage.py file"
    [ -f "requirements.txt" ] && echo "  - requirements.txt file"
    [ -f ".env" ] && echo "  - .env file"
    [ -d "venv" ] && echo "  - Virtual environment: venv/"
    [ -d "middlewares" ] && echo "  - Middlewares directory"
    echo ""
    
    while true; do
        read -p "Do you want to overwrite the existing files? (y/n): " -n 1 -r
        echo
        case $REPLY in
            [Yy]* )
                echo "Overwriting existing project files..."
                # Remove existing files and directories
                [ -d "$PROJECT_NAME" ] && rm -rf "$PROJECT_NAME"
                [ -f "manage.py" ] && rm -f "manage.py"
                [ -f "requirements.txt" ] && rm -f "requirements.txt"
                [ -f ".env" ] && rm -f ".env"
                [ -f ".env.sample" ] && rm -f ".env.sample"
                [ -f "deploy.sh" ] && rm -f "deploy.sh"
                [ -f ".gitignore" ] && rm -f ".gitignore"
                [ -d "middlewares" ] && rm -rf "middlewares"
                [ -d "templates" ] && rm -rf "templates"
                [ -d "static" ] && rm -rf "static"
                [ -d "media" ] && rm -rf "media"
                [ -d "logs" ] && rm -rf "logs"
                [ -f "db.sqlite3" ] && rm -f "db.sqlite3"
                echo "Existing files removed."
                break
                ;;
            [Nn]* )
                echo "Project creation cancelled. Existing files preserved."
                exit 0
                ;;
            * )
                echo "Please answer y (yes) or n (no)."
                ;;
        esac
    done
fi

echo "Starting Django project creation for: $PROJECT_NAME"
echo "Base directory: $BASE_DIR"

# Step 1: Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Step 2: Install Django and create basic project
echo "Installing Django and creating project..."
pip install --upgrade pip
pip install setuptools wheel
pip install Django==5.2.2
pip install python-decouple

# Create Django project
django-admin startproject $PROJECT_NAME .

# Step 3: Reorganize project structure
echo "Reorganizing project structure..."

# Create the nested structure: project_name/project_name/
mkdir -p "$PROJECT_NAME/$PROJECT_NAME"
mkdir -p "$PROJECT_NAME/$PROJECT_NAME/settings"
mkdir -p "$PROJECT_NAME/apps/common"
mkdir -p "middlewares"
mkdir -p "templates/email_templates"
mkdir -p "static"
mkdir -p "media"
mkdir -p "logs"

# Move files to nested structure
mv "$PROJECT_NAME/settings.py" "$PROJECT_NAME/$PROJECT_NAME/settings/base_settings.py"
mv "$PROJECT_NAME/urls.py" "$PROJECT_NAME/$PROJECT_NAME/urls.py"
mv "$PROJECT_NAME/wsgi.py" "$PROJECT_NAME/$PROJECT_NAME/wsgi.py"
mv "$PROJECT_NAME/asgi.py" "$PROJECT_NAME/$PROJECT_NAME/asgi.py"
mv "$PROJECT_NAME/__init__.py" "$PROJECT_NAME/$PROJECT_NAME/__init__.py"

# Keep manage.py in the root directory (don't move it)

# Step 4: Create Django app using django-admin
echo "Creating common app..."
run_django_command python manage.py startapp common $PROJECT_NAME/apps/common

# Step 5: Create configuration files
echo "Creating configuration files..."

# Create configurations.py
cat > "$PROJECT_NAME/configurations.py" << EOF
from decouple import config, Csv

# Basic settings
BASE_PREFIX = config('BASE_PREFIX', default='')
DEBUG = config('DEBUG', default=True, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# Email settings
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@${PROJECT_NAME}.com')

# Social Authentication
ENABLE_SOCIAL_AUTH = config('ENABLE_SOCIAL_AUTH', default=False, cast=bool)
SOCIAL_AUTH_FACEBOOK_SCOPE = config('SOCIAL_AUTH_FACEBOOK_SCOPE', default='email')
SOCIAL_AUTH_FACEBOOK_SECRET = config('SOCIAL_AUTH_FACEBOOK_SECRET', default='')
SOCIAL_AUTH_FACEBOOK_KEY = config('SOCIAL_AUTH_FACEBOOK_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = config('SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE', default='openid email profile')
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')

# Cloudinary settings
CLOUDINARY_CLOUD_NAME = config('CLOUDINARY_CLOUD_NAME', default='')
CLOUDINARY_API_KEY = config('CLOUDINARY_API_KEY', default='')
CLOUDINARY_API_SECRET = config('CLOUDINARY_API_SECRET', default='')

# Database settings
DB_HOST_NAME = config('DB_HOST_NAME', default='localhost')
DB_PORT = config('DB_PORT', default=5432, cast=int)
DB_NAME = config('DB_NAME', default='${PROJECT_NAME}_db')
DB_USER_NAME = config('DB_USER_NAME', default='postgres')
DB_PASSWORD = config('DB_PASSWORD', default='')
DATABASE_URL = config('DATABASE_URL', default=f'postgresql://{DB_USER_NAME}:{DB_PASSWORD}@{DB_HOST_NAME}:{DB_PORT}/{DB_NAME}')

# Redis settings
REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')

# Stripe settings
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Celery settings
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')

# Security settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = config('SECURE_PROXY_SSL_HEADER', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)

# Logging
LOG_LEVEL = config('LOG_LEVEL', default='INFO')
EOF

# Create base_settings.py with project-specific configurations
cat > "$PROJECT_NAME/$PROJECT_NAME/settings/base_settings.py" << EOF
"""
Django settings for $PROJECT_NAME project.

Generated by 'django-admin startproject' using Django 5.2.2.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import os
from pathlib import Path
from datetime import timedelta
from corsheaders.defaults import default_headers

from ${PROJECT_NAME}.configurations import (
    ENABLE_SOCIAL_AUTH,
    SECRET_KEY,
    ALLOWED_HOSTS,
    BASE_PREFIX,
    DEBUG,
    EMAIL_BACKEND,
    EMAIL_HOST,
    EMAIL_HOST_PASSWORD,
    EMAIL_HOST_USER,
    EMAIL_PORT,
    EMAIL_USE_TLS,
    DEFAULT_FROM_EMAIL,
    SOCIAL_AUTH_FACEBOOK_SCOPE,
    SOCIAL_AUTH_FACEBOOK_SECRET,
    SOCIAL_AUTH_FACEBOOK_KEY,
    SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
    SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
    SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE,
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
    DATABASE_URL,
    REDIS_URL,
    STRIPE_SECRET_KEY,
    STRIPE_PUBLISHABLE_KEY,
    STRIPE_WEBHOOK_SECRET,
    CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND,
    LOG_LEVEL
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = DEBUG

ALLOWED_HOSTS = ALLOWED_HOSTS

CORS_ALLOW_HEADERS = list(default_headers) + [
    "ngrok-skip-browser-warning",
]

SESSION_COOKIE_SAMESITE = None
SESSION_COOKIE_SECURE = True

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = ["http://localhost:5173",]
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_SAMESITE = 'None'

EMAIL_HOST = EMAIL_HOST
EMAIL_PORT = EMAIL_PORT
EMAIL_USE_TLS = EMAIL_USE_TLS
EMAIL_HOST_USER = EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = EMAIL_HOST_PASSWORD
DEFAULT_FROM_EMAIL = DEFAULT_FROM_EMAIL
SOCIAL_AUTH_FACEBOOK_KEY = SOCIAL_AUTH_FACEBOOK_KEY
SOCIAL_AUTH_FACEBOOK_SECRET = SOCIAL_AUTH_FACEBOOK_SECRET
SOCIAL_AUTH_FACEBOOK_SCOPE = SOCIAL_AUTH_FACEBOOK_SCOPE
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = SOCIAL_AUTH_GOOGLE_OAUTH2_KEY
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE

# Application definition
INSTALLED_APPS = [
    # my apps
    '${PROJECT_NAME}.apps.common',
    # Third party apps
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'drf_spectacular',
    'django_filters',
    'cloudinary_storage',
    'cloudinary',
    'django_redis',
    'djoser',
    'social_django',
    # Django's default apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'middlewares.user_middleware.CurrentUserMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middlewares.response_middleware.APIResponseMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

if ENABLE_SOCIAL_AUTH:
    AUTHENTICATION_BACKENDS += [
        'social_core.backends.facebook.FacebookOAuth2',
        'social_core.backends.google.GoogleOAuth2',
    ]

SPECTACULAR_SETTINGS = {
    'TITLE': '${PROJECT_NAME^} API',
    'DESCRIPTION': 'API documentation for the ${PROJECT_NAME^} project',
    'VERSION': '1.0.0',
}

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=48),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

ROOT_URLCONF = '${PROJECT_NAME}.${PROJECT_NAME}.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT, 'templates')],
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

# Default database configuration (can be overridden in dev/prod settings)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

WSGI_APPLICATION = '${PROJECT_NAME}.${PROJECT_NAME}.wsgi.application'

CELERY_BROKER_URL = CELERY_BROKER_URL
CELERY_RESULT_BACKEND = CELERY_RESULT_BACKEND
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",  # Use DB 2 for cache
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# Stripe Configuration
STRIPE_SECRET_KEY = STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY = STRIPE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET = STRIPE_WEBHOOK_SECRET

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
    'API_KEY': CLOUDINARY_API_KEY,
    'API_SECRET': CLOUDINARY_API_SECRET,
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Import cloudinary after settings are defined to avoid circular imports
import cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
)

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = 'static/'

MEDIA_URL = 'media/'
MEDIA_ROOT = 'media/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

BASE_PREFIX = BASE_PREFIX

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(PROJECT_ROOT, 'logs', 'django.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'level': LOG_LEVEL,
        'handlers': ['console', 'file'],
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        '${PROJECT_NAME}': {
            'handlers': ['console', 'file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}
EOF

# Create dev_settings.py
cat > "$PROJECT_NAME/$PROJECT_NAME/settings/dev_settings.py" << EOF
from .base_settings import *
import os

# Override DEBUG to ensure it's True in development
DEBUG = True

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
print("Using local SQLite as database and email will be seen on the console.")

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Use console for development

# Override any database configuration from base_settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Ensure we're not using any dummy database configuration
DATABASE_URL = None
EOF

# Create prod_settings.py
cat > "$PROJECT_NAME/$PROJECT_NAME/settings/prod_settings.py" << EOF
from .base_settings import *
import dj_database_url


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

EMAIL_BACKEND = EMAIL_BACKEND

DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
EOF

# Create settings/__init__.py
cat > "$PROJECT_NAME/$PROJECT_NAME/settings/__init__.py" << EOF
"""
Settings package init file.
"""
EOF

# Create updated manage.py
cat > "manage.py" << EOF
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Check for DEBUG environment variable first, then import configurations
    debug_env = os.environ.get('DEBUG', '').lower() in ('true', '1', 'yes', 'on')
    
    if debug_env:
        # Force development settings when DEBUG=True in environment
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${PROJECT_NAME}.${PROJECT_NAME}.settings.dev_settings')
    else:
        # Import configurations to check DEBUG setting from .env file
        try:
            from ${PROJECT_NAME}.configurations import DEBUG
            if DEBUG:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${PROJECT_NAME}.${PROJECT_NAME}.settings.dev_settings')
            else:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${PROJECT_NAME}.${PROJECT_NAME}.settings.prod_settings')
        except ImportError:
            # Fallback to development settings if import fails
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${PROJECT_NAME}.${PROJECT_NAME}.settings.dev_settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
EOF

# Create URLs configuration
cat > "$PROJECT_NAME/$PROJECT_NAME/urls.py" << EOF
"""
URL Configuration for $PROJECT_NAME project.

The \`urlpatterns\` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenRefreshView

# Base URL patterns without prefix
urlpatterns = [
    path('admin/', admin.site.urls),
    path('social/', include('social_django.urls', namespace='social')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Add a prefix for deployment (e.g., 'dev' or 'prod') if BASE_PREFIX is set
from django.conf import settings

base_prefix = getattr(settings, 'BASE_PREFIX', '')
if base_prefix:
    # Create prefixed patterns by wrapping the existing patterns
    prefixed_patterns = [path(f'{base_prefix}/', include(urlpatterns))]
    urlpatterns = prefixed_patterns
EOF

# Create WSGI configuration
cat > "$PROJECT_NAME/$PROJECT_NAME/wsgi.py" << EOF
"""
WSGI config for $PROJECT_NAME project.

It exposes the WSGI callable as a module-level variable named \`\`application\`\`.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from ${PROJECT_NAME}.configurations import DEBUG

from django.core.wsgi import get_wsgi_application

if DEBUG:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "${PROJECT_NAME}.${PROJECT_NAME}.settings.dev_settings")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "${PROJECT_NAME}.${PROJECT_NAME}.settings.prod_settings")

application = get_wsgi_application()
EOF

# Create ASGI configuration
cat > "$PROJECT_NAME/$PROJECT_NAME/asgi.py" << EOF
"""
ASGI config for $PROJECT_NAME project.

It exposes the ASGI callable as a module-level variable named \`\`application\`\`.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from ${PROJECT_NAME}.configurations import DEBUG

from django.core.asgi import get_asgi_application

if DEBUG:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "${PROJECT_NAME}.${PROJECT_NAME}.settings.dev_settings")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "${PROJECT_NAME}.${PROJECT_NAME}.settings.prod_settings")

application = get_asgi_application()
EOF

# Create Celery configuration
cat > "$PROJECT_NAME/$PROJECT_NAME/celery.py" << EOF
import os
from celery import Celery
from ${PROJECT_NAME}.configurations import DEBUG

# Set the default Django settings module
if DEBUG:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${PROJECT_NAME}.${PROJECT_NAME}.settings.dev_settings')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${PROJECT_NAME}.${PROJECT_NAME}.settings.prod_settings')

app = Celery('${PROJECT_NAME}')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
EOF

# Create updated __init__.py with Celery
cat > "$PROJECT_NAME/__init__.py" << EOF
"""
${PROJECT_NAME^} project init file.
"""
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from ${PROJECT_NAME}.${PROJECT_NAME}.celery import app as celery_app

__all__ = ('celery_app',)
EOF

# Step 6: Create middleware files
echo "Creating middleware files..."

# Create user middleware
cat > "middlewares/user_middleware.py" << EOF
import threading
from django.contrib.auth import get_user_model

_user_local = threading.local()
User = get_user_model()


class CurrentUserMiddleware:
    """
    Middleware to store the current user in thread-local storage.
    This allows access to the current user from anywhere in the application.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store the current user in thread-local storage
        _user_local.user = getattr(request, 'user', None)
        
        response = self.get_response(request)
        
        # Clean up thread-local storage
        if hasattr(_user_local, 'user'):
            del _user_local.user
            
        return response


def get_current_user():
    """
    Get the current user from thread-local storage.
    Returns None if no user is available.
    """
    return getattr(_user_local, 'user', None)
EOF

# Create response middleware
cat > "middlewares/response_middleware.py" << EOF
import json
from django.http import JsonResponse
from django.core.exceptions import ValidationError as DjangoValidationError


class APIResponseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Skip processing for redirect responses (300–399)
        if 300 <= response.status_code < 400:
            return response

        # Handle permission errors (403)
        if response.status_code == 403:
            try:
                content = json.loads(response.content) if response.content else {}
                detail = content.get('detail', response.reason_phrase)
            except json.JSONDecodeError:
                detail = response.reason_phrase
            return JsonResponse({
                "response_status": "error",
                "response_description": f"Forbidden: {detail}",
                "response_data": {"detail": detail}
            }, status=403)

        # Handle validation errors (400)
        if response.status_code == 400:
            try:
                content = json.loads(response.content) if response.content else {}
                detail = content.get('detail', content)
            except json.JSONDecodeError:
                detail = response.reason_phrase
            return JsonResponse({
                "response_status": "error",
                "response_description": "Validation error occurred.",
                "response_data": detail
            }, status=400)

        # Check if the response is already a JsonResponse
        if isinstance(response, JsonResponse):
            content = json.loads(response.content)
            # Add standard fields if not already present
            if "response_status" not in content:
                standardized_response = {
                    "response_status": "success" if response.status_code <= 399 else "error",
                    "response_description": content.get("message", "Request processed"),
                    "response_data": content.get("data", content)
                }
                return JsonResponse(standardized_response, status=response.status_code)

        # Handle other error responses
        if response.status_code > 399:
            return JsonResponse({
                "response_status": "error",
                "response_description": response.reason_phrase,
                "response_data": {}
            }, status=response.status_code)

        return response
EOF

# Create middleware __init__.py
cat > "middlewares/__init__.py" << EOF
"""
Middlewares package init file.
"""
EOF

# Step 7: Create common app files
echo "Creating common app files..."

# Update common app's apps.py
cat > "$PROJECT_NAME/apps/common/apps.py" << EOF
from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '${PROJECT_NAME}.apps.common'
EOF

# Create models.py for common app
cat > "$PROJECT_NAME/apps/common/models.py" << EOF
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class BaseModel(models.Model):
    """
    Abstract base model with common fields for all models.
    """
    id = models.CharField(max_length=26, primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        if not self.id:
            # Generate a unique ID (you can use ulid or uuid)
            import time
            import random
            import string
            timestamp = int(time.time() * 1000)
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            self.id = f"{timestamp:013d}{random_part}"
        super().save(*args, **kwargs)


class TimestampMixin(models.Model):
    """
    Mixin to add timestamp fields to models.
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the record was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the record was last updated")
    
    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Mixin to add soft delete functionality to models.
    """
    is_deleted = models.BooleanField(default=False, help_text="Indicates if the record is soft deleted")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the record was soft deleted")
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Soft delete the instance."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        """Restore a soft deleted instance."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class StatusChoices(models.TextChoices):
    """
    Common status choices for models.
    """
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    PENDING = 'pending', 'Pending'
    SUSPENDED = 'suspended', 'Suspended'


# Example model using the mixins
class CommonSettings(BaseModel, TimestampMixin, SoftDeleteMixin):
    """
    Model to store application-wide settings.
    """
    key = models.CharField(max_length=255, unique=True, help_text="Setting key")
    value = models.TextField(help_text="Setting value")
    description = models.TextField(blank=True, help_text="Description of the setting")
    is_public = models.BooleanField(default=False, help_text="Whether this setting is public")
    
    class Meta:
        db_table = '${PROJECT_NAME}_common_settings'
        verbose_name = 'Common Setting'
        verbose_name_plural = 'Common Settings'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."
EOF

# Create filters.py for common app
cat > "$PROJECT_NAME/apps/common/filters.py" << EOF
import django_filters
from django.db import models
from django_filters import rest_framework as filters


class BaseFilterSet(filters.FilterSet):
    """
    Base filter set with common filtering options.
    """
    created_at_gte = filters.DateTimeFilter(field_name="created_at", lookup_expr='gte', label="Created after")
    created_at_lte = filters.DateTimeFilter(field_name="created_at", lookup_expr='lte', label="Created before")
    updated_at_gte = filters.DateTimeFilter(field_name="updated_at", lookup_expr='gte', label="Updated after")
    updated_at_lte = filters.DateTimeFilter(field_name="updated_at", lookup_expr='lte', label="Updated before")
    
    # Search functionality
    search = filters.CharFilter(method='filter_search', label="Search")
    
    class Meta:
        abstract = True
    
    def filter_search(self, queryset, name, value):
        """
        Override this method in child classes to implement custom search logic.
        """
        return queryset


class CommonSettingsFilterSet(BaseFilterSet):
    """
    Filter set for CommonSettings model.
    """
    key = filters.CharFilter(field_name="key", lookup_expr='icontains', label="Key contains")
    value = filters.CharFilter(field_name="value", lookup_expr='icontains', label="Value contains")
    is_public = filters.BooleanFilter(field_name="is_public", label="Is public")
    is_deleted = filters.BooleanFilter(field_name="is_deleted", label="Is deleted")
    
    class Meta:
        model = None  # Will be set when imported
        fields = ['key', 'value', 'is_public', 'is_deleted']
    
    def filter_search(self, queryset, name, value):
        """
        Search in key, value, and description fields.
        """
        return queryset.filter(
            models.Q(key__icontains=value) |
            models.Q(value__icontains=value) |
            models.Q(description__icontains=value)
        )


class DateRangeFilter(filters.FilterSet):
    """
    Generic date range filter that can be used with any model.
    """
    date_from = filters.DateFilter(method='filter_date_from', label="Date from")
    date_to = filters.DateFilter(method='filter_date_to', label="Date to")
    
    def filter_date_from(self, queryset, name, value):
        """Filter records from the specified date."""
        return queryset.filter(created_at__date__gte=value)
    
    def filter_date_to(self, queryset, name, value):
        """Filter records up to the specified date."""
        return queryset.filter(created_at__date__lte=value)


class StatusFilter(filters.FilterSet):
    """
    Generic status filter for models with status fields.
    """
    status = filters.CharFilter(field_name="status", lookup_expr='exact', label="Status")
    status_in = filters.CharFilter(method='filter_status_in', label="Status in (comma separated)")
    
    def filter_status_in(self, queryset, name, value):
        """Filter by multiple status values."""
        if value:
            status_list = [status.strip() for status in value.split(',')]
            return queryset.filter(status__in=status_list)
        return queryset


# Utility functions for common filtering patterns
def get_boolean_filter_choices():
    """Get choices for boolean filters."""
    return [
        ('true', 'Yes'),
        ('false', 'No'),
    ]


def get_ordering_filter_fields():
    """Get common ordering fields."""
    return ['created_at', '-created_at', 'updated_at', '-updated_at', 'id', '-id']
EOF

# Create permissions.py for common app
cat > "$PROJECT_NAME/apps/common/permissions.py" << EOF
from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    message = "You must be the owner of this object to modify it."

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.created_by == request.user if hasattr(obj, 'created_by') else True


class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to only allow admins to modify objects.
    """
    message = "You must be an admin to modify this object."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsSuperUserOnly(BasePermission):
    """
    Permission to allow only superusers to access the endpoint.
    """
    message = "You must be a superuser to access this endpoint."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsStaffOrReadOnly(BasePermission):
    """
    Permission to allow only staff members to modify objects.
    """
    message = "You must be a staff member to modify this object."

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class IsAuthenticatedOrCreateOnly(BasePermission):
    """
    Permission to allow unauthenticated users to create objects,
    but require authentication for other operations.
    """
    message = "Authentication required for this operation."

    def has_permission(self, request, view):
        if request.method == 'POST':
            return True
        return request.user and request.user.is_authenticated


class IsOwnerOrAdmin(BasePermission):
    """
    Permission to allow owners or admins to access/modify objects.
    """
    message = "You must be the owner or an admin to access this object."

    def has_object_permission(self, request, view, obj):
        # Admin can access/modify any object
        if request.user and request.user.is_staff:
            return True
        
        # Owner can access/modify their own object
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        
        return False


class ReadOnlyPermission(BasePermission):
    """
    Permission that only allows read-only access.
    """
    message = "Read-only access."

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsActiveUser(BasePermission):
    """
    Permission to check if user is active.
    """
    message = "Your account is not active."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_active


class HasGroupPermission(BasePermission):
    """
    Permission to check if user belongs to a specific group.
    Usage: Add required_groups attribute to the view.
    """
    message = "You don't have the required group permissions."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        required_groups = getattr(view, 'required_groups', None)
        if not required_groups:
            return True
        
        user_groups = request.user.groups.values_list('name', flat=True)
        return any(group in user_groups for group in required_groups)


class DynamicPermission(BasePermission):
    """
    Dynamic permission class that can be configured per view.
    Usage: Add permission_classes_by_action to the view.
    """
    
    def has_permission(self, request, view):
        action = getattr(view, 'action', None)
        permission_classes_by_action = getattr(view, 'permission_classes_by_action', {})
        
        if action in permission_classes_by_action:
            for permission_class in permission_classes_by_action[action]:
                permission = permission_class()
                if not permission.has_permission(request, view):
                    self.message = getattr(permission, 'message', 'Permission denied.')
                    return False
        
        return True


# Utility functions for permission checking
def user_has_permission(user, permission_name):
    """
    Check if user has a specific permission.
    """
    return user.has_perm(permission_name) if user and user.is_authenticated else False


def user_in_group(user, group_name):
    """
    Check if user is in a specific group.
    """
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=group_name).exists()


def is_object_owner(user, obj):
    """
    Check if user is the owner of an object.
    """
    if not user or not user.is_authenticated:
        return False
    
    # Check various owner fields
    owner_fields = ['created_by', 'user', 'owner', 'author']
    for field in owner_fields:
        if hasattr(obj, field):
            return getattr(obj, field) == user
    
    return False
EOF

# Create pagination.py for common app
cat > "$PROJECT_NAME/apps/common/pagination.py" << EOF
from rest_framework.pagination import PageNumberPagination
from django.http import JsonResponse


class GenericPagination(PageNumberPagination):
    page_size = 10  # Default number of items per page
    page_size_query_param = 'page_size'  # Query parameter to control page size
    max_page_size = 100  # Maximum allowed page size to prevent large responses

    def get_paginated_response(self, data):
        """
        Returns a paginated response in the format: {"message": str, "data": dict}.
        
        Args:
            data: The serialized data for the current page.
        
        Returns:
            JsonResponse: A response containing pagination metadata and results.
        """
        # Use a default or provided message for the paginated response
        message = getattr(self, 'custom_message', "Data retrieved successfully.")
        return JsonResponse({
            "message": message,
            "data": {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data
            }
        }, status=200)
EOF

# Create apps/__init__.py
cat > "$PROJECT_NAME/apps/__init__.py" << EOF
"""
Apps package init file.
"""
EOF

# Step 8: Create requirements.txt
echo "Creating requirements.txt..."
cat > "requirements.txt" << EOF
# Essential packages
setuptools>=65.0.0
wheel

# Django Framework
Django==5.2.2
asgiref==3.8.1
sqlparse==0.5.0
tzdata==2024.1

# Django REST Framework and JWT
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.0
PyJWT==2.8.0

# API Documentation
drf-spectacular==0.27.2
PyYAML==6.0.1
uritemplate==4.1.1

# CORS Headers
django-cors-headers==4.4.0

# Database
dj-database-url==2.2.0
psycopg2-binary==2.9.9

# Redis and Caching
redis==5.0.7
django-redis==5.4.0

# Celery for async tasks
celery==5.3.4
kombu==5.3.4
billiard==4.2.0

# Social Authentication
social-auth-app-django==5.4.2
social-auth-core==4.5.4

# Djoser for authentication
djoser==2.2.3

# Cloud Storage (Cloudinary)
cloudinary==1.40.0
django-cloudinary-storage==0.3.0

# Image Processing
Pillow==10.4.0

# Environment Configuration
python-decouple==3.8

# Filters
django-filter==24.3

# Google OAuth
google-auth==2.32.0
google-auth-oauthlib==1.2.1
google-auth-httplib2==0.2.0

# Stripe for payments
stripe==10.8.0

# HTTP Requests
requests==2.32.3
urllib3==2.2.2

# Cryptography
cryptography==43.0.0

# Other utilities
certifi==2024.7.4
charset-normalizer==3.3.2
idna==3.7
six==1.16.0
pytz==2024.1

# Development dependencies (optional)
# Uncomment for development
# django-debug-toolbar==4.4.6
# ipython==8.26.0
EOF

# Step 9: Create .env.sample
echo "Creating .env.sample..."
cat > ".env.sample" << EOF
# Basic Django Settings
BASE_PREFIX=dev
DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production-#@$%^&*()
ALLOWED_HOSTS=127.0.0.1,localhost,${PROJECT_NAME}.cloud

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@${PROJECT_NAME}.com

# Social Authentication
ENABLE_SOCIAL_AUTH=False
SOCIAL_AUTH_FACEBOOK_KEY=your-facebook-app-id
SOCIAL_AUTH_FACEBOOK_SECRET=your-facebook-app-secret
SOCIAL_AUTH_FACEBOOK_SCOPE=email
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=your-google-oauth2-client-id
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=your-google-oauth2-client-secret
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE=openid email profile
GOOGLE_CLIENT_ID=your-google-client-id

# Cloudinary Settings (Media Storage)
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret

# Database Configuration (PostgreSQL)
DB_HOST_NAME=localhost
DB_PORT=5432
DB_NAME=${PROJECT_NAME}_db
DB_USER_NAME=postgres
DB_PASSWORD=your-database-password

# Redis Configuration (for caching and Celery)
REDIS_URL=redis://127.0.0.1:6379/0

# Stripe Payment Configuration
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key
STRIPE_WEBHOOK_SECRET=whsec_your-stripe-webhook-secret

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security Settings (for production)
SECURE_SSL_REDIRECT=False
SECURE_PROXY_SSL_HEADER=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# Logging Level
LOG_LEVEL=DEBUG
EOF

# Step 9: Create .env
echo "Creating .env..."
cat > ".env" << EOF
# Basic Django Settings
DEBUG=True
EOF

# Step 10: Create deployment script
cat > "deploy.sh" << EOF
#!/bin/bash

# Configuration
PROJECT_DIR="/home/\$USER/${PROJECT_NAME}-backend"
VENV_PATH="\$PROJECT_DIR/venv"
REPO_URL="https://github.com/YourUsername/${PROJECT_NAME}-backend.git"  # Replace with your repo URL
BRANCH="main"  # Replace with your branch name
GUNICORN_SERVICE="gunicorn_${PROJECT_NAME}"
NGINX_SERVICE="nginx"

# Exit on any error
set -e

echo "Starting deployment process for ${PROJECT_NAME}..."

# Step 1: Ensure PostgreSQL dependencies
echo "Installing PostgreSQL dependencies..."
sudo apt update
sudo apt install -y libpq-dev python3-dev

# Step 2: Navigate to project directory
cd "\$PROJECT_DIR" || { echo "Failed to navigate to \$PROJECT_DIR"; exit 1; }

# Step 3: Pull updates from Git
echo "Pulling updates from Git repository..."
git fetch origin
git checkout "\$BRANCH"
git pull origin "\$BRANCH" || { echo "Git pull failed"; exit 1; }

# Step 4: Activate virtual environment
echo "Activating virtual environment..."
source "\$VENV_PATH/bin/activate" || { echo "Failed to activate virtual environment"; exit 1; }

# Step 5: Install requirements
echo "Installing dependencies..."
pip install --upgrade pip
cd ${PROJECT_NAME}
pip install -r ../requirements.txt || { echo "Failed to install requirements"; exit 1; }

# Step 6: Run migrations
echo "Running Django migrations..."
python manage.py makemigrations || { echo "Makemigrations failed"; exit 1; }
python manage.py migrate || { echo "Migrate failed"; exit 1; }

# Step 7: Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || { echo "Collectstatic failed"; exit 1; }

# Step 8: Set permissions for static files and socket
echo "Setting permissions..."
sudo chown -R \$USER:www-data "\$PROJECT_DIR/staticfiles"
sudo chmod -R 755 "\$PROJECT_DIR/staticfiles"
sudo chown \$USER:www-data "\$PROJECT_DIR/gunicorn.sock"
sudo chmod 660 "\$PROJECT_DIR/gunicorn.sock"

# Step 9: Ensure Redis is installed and running
echo "Installing and starting Redis..."
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
sudo systemctl status redis-server --no-pager

# Step 10: Restart Gunicorn and Nginx
echo "Restarting Gunicorn and Nginx..."
sudo systemctl restart "\$GUNICORN_SERVICE" || { echo "Failed to restart Gunicorn"; exit 1; }
sudo systemctl restart "\$NGINX_SERVICE" || { echo "Failed to restart Nginx"; exit 1; }

# Step 11: Verify services
echo "Checking service status..."
sudo systemctl status "\$GUNICORN_SERVICE" --no-pager
sudo systemctl status "\$NGINX_SERVICE" --no-pager

echo "Deployment completed successfully for ${PROJECT_NAME}!"
EOF

# Make deploy.sh executable
chmod +x "deploy.sh"

# Step 12: Create .gitignore
echo "Creating .gitignore..."
cat > ".gitignore" << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
media/
staticfiles/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# Virtual environment
venv/
env/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs/
*.log

# Redis dump
dump.rdb

# Celery
celerybeat-schedule
celerybeat.pid

# Coverage
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/
EOF

# Step 13: Run initial migrations
echo "Running initial migrations..."
# Django commands should be run from the root directory where manage.py is located
run_django_command python manage.py makemigrations
run_django_command python manage.py migrate

# Step 14: Create superuser (optional)
read -p "Do you want to create a superuser? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    run_django_command python manage.py createsuperuser
fi

echo "=============================================="
echo "Django project '$PROJECT_NAME' has been created successfully!"
echo ""
echo "Project structure:"
echo "├── $PROJECT_NAME/"
echo "│   ├── $PROJECT_NAME/"
echo "│   │   ├── settings/"
echo "│   │   │   ├── __init__.py"
echo "│   │   │   ├── base_settings.py"
echo "│   │   │   ├── dev_settings.py"
echo "│   │   │   └── prod_settings.py"
echo "│   │   ├── __init__.py"
echo "│   │   ├── configurations.py"
echo "│   │   ├── urls.py"
echo "│   │   ├── wsgi.py"
echo "│   │   ├── asgi.py"
echo "│   │   └── celery.py"
echo "│   ├── apps/"
echo "│   │   ├── __init__.py"
echo "│   │   └── common/"
echo "│   │       ├── __init__.py"
echo "│   │       ├── admin.py"
echo "│   │       ├── apps.py"
echo "│   │       ├── models.py"
echo "│   │       ├── filters.py"
echo "│   │       ├── permissions.py"
echo "│   │       ├── tests.py"
echo "│   │       └── views.py"
echo "├── middlewares/"
echo "│   ├── __init__.py"
echo "│   ├── user_middleware.py"
echo "│   └── response_middleware.py"
echo "├── templates/"
echo "├── static/"
echo "├── media/"
echo "├── logs/"
echo "├── venv/"
echo "├── manage.py"
echo "├── requirements.txt"
echo "├── .env.sample"
echo "├── deploy.sh"
echo "└── .gitignore"
echo ""
echo "Next steps:"
echo "1. Copy .env.sample to .env and configure your environment variables"
echo "2. Run: python manage.py runserver"
echo "3. Visit: http://127.0.0.1:8000/dev/api/schema/redoc/ for API documentation"
echo ""
echo "Happy coding $PROJECT_NAME backend!"
echo "=============================================="
