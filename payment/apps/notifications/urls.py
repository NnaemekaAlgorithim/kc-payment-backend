from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'devices', views.FCMDeviceViewSet, basename='fcm-device')
router.register(r'preferences', views.NotificationPreferenceViewSet, basename='notification-preference')

app_name = 'notifications'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
]

# Generated URL patterns from the router:
# 
# Notification Operations:
# GET    /api/notifications/                     - List user's notifications
# GET    /api/notifications/{id}/                - Get specific notification details
# POST   /api/notifications/mark_read/           - Mark notifications as read
# GET    /api/notifications/statistics/          - Get notification statistics
#
# FCM Device Operations:  
# GET    /api/devices/                           - List user's registered devices
# POST   /api/devices/                           - Register new FCM device
# GET    /api/devices/{id}/                      - Get device details
# PUT    /api/devices/{id}/                      - Update device info
# DELETE /api/devices/{id}/                     - Remove device
# POST   /api/devices/{id}/activate/             - Activate device
# POST   /api/devices/{id}/deactivate/           - Deactivate device
#
# Notification Preference Operations:
# GET    /api/preferences/                       - Get user's preferences (auto-creates if missing)
# PUT    /api/preferences/{id}/                  - Update preferences
# PATCH  /api/preferences/{id}/                  - Partially update preferences
