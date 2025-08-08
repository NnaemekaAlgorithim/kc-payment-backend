from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings


@require_http_methods(["GET"])
def api_root(request):
    """
    API root endpoint that provides information about available endpoints
    """
    base_prefix = getattr(settings, 'BASE_PREFIX', '')
    base_url = f"/{base_prefix}" if base_prefix else ""
    
    return JsonResponse({
        "message": "Welcome to KC Payment Backend API",
        "version": "1.0.0",
        "endpoints": {
            "admin": f"{base_url}/admin/",
            "api_schema": f"{base_url}/api/schema/",
            "api_docs": f"{base_url}/api/schema/redoc/",
            "auth": {
                "register": f"{base_url}/api/v1/auth/register/",
                "login": f"{base_url}/api/v1/auth/login/",
                "activate": f"{base_url}/api/v1/auth/activate/",
                "forgot_password": f"{base_url}/api/v1/auth/forgot-password/",
                "reset_password": f"{base_url}/api/v1/auth/reset-password/",
                "refresh_token": f"{base_url}/api/token/refresh/",
            },
            "user": {
                "profile": f"{base_url}/api/v1/profile/",
                "users_list": f"{base_url}/api/v1/users/",
            }
        }
    })


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint
    """
    return JsonResponse({
        "status": "healthy",
        "service": "KC Payment Backend"
    })
