from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Create a router for the UserViewSet
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

# Define URL patterns
urlpatterns = [
    # Include router URLs
    path('api/v1/', include(router.urls)),
    
    # Custom endpoint aliases for better API naming
    path('api/v1/auth/register/', UserViewSet.as_view({'post': 'register'}), name='auth-register'),
    path('api/v1/auth/activate/', UserViewSet.as_view({'post': 'activate'}), name='auth-activate'),
    path('api/v1/auth/login/', UserViewSet.as_view({'post': 'login'}), name='auth-login'),
    path('api/v1/auth/forgot-password/', UserViewSet.as_view({'post': 'forgot_password'}), name='auth-forgot-password'),
    path('api/v1/auth/reset-password/', UserViewSet.as_view({'post': 'reset_password'}), name='auth-reset-password'),
    path('api/v1/profile/', UserViewSet.as_view({'get': 'profile', 'put': 'update_profile', 'patch': 'update_profile'}), name='user-profile'),
]

app_name = 'users'
