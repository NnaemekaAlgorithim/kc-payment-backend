"""
URL Configuration for payment project.

The `urlpatterns` list routes URLs to views. For more information please see:
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
    
    # ReDoc documentation at root
    path('', SpectacularRedocView.as_view(url_name='schema'), name='root-redoc'),
    
    # App URLs
    path('', include('payment.apps.common.urls', namespace='common')),
    path('', include('payment.apps.users.urls', namespace='users')),
    path('', include('payment.apps.transactions.urls', namespace='transactions')),
]

# Add a prefix for deployment (e.g., 'dev' or 'prod') if BASE_PREFIX is set
from django.conf import settings

base_prefix = getattr(settings, 'BASE_PREFIX', '')
if base_prefix:
    # Create prefixed patterns by wrapping the existing patterns
    prefixed_patterns = [path(f'{base_prefix}/', include(urlpatterns))]
    urlpatterns = prefixed_patterns
