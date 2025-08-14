from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.openapi import OpenApiTypes

from .models import Notification, FCMDevice, NotificationPreference, NotificationStatus
from .serializers import (
    NotificationSerializer,
    FCMDeviceSerializer,
    NotificationPreferenceSerializer,
    MarkNotificationReadSerializer
)
from .services import notification_service


class NotificationPagination(PageNumberPagination):
    """Pagination for notifications."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user notifications.
    
    Allows users to:
    - View their notifications
    - Mark notifications as read
    - Get notification statistics
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['notification_type', 'status', 'transaction_id']
    ordering = ['-created_at']
    ordering_fields = ['created_at', 'sent_at', 'read_at']
    
    def get_queryset(self):
        """Return notifications for the current user."""
        return Notification.objects.filter(recipient=self.request.user)
    
    @extend_schema(
        summary="List user notifications",
        description="""
        Get paginated list of notifications for the authenticated user.
        
        **Features:**
        - Filter by notification type, status, or transaction ID
        - Order by creation date, sent date, or read date
        - Paginated results (20 per page by default)
        
        **Query Parameters:**
        - `unread_only=true` - Show only unread notifications
        - `notification_type` - Filter by notification type
        - `status` - Filter by notification status
        """,
        parameters=[
            OpenApiParameter(
                name='unread_only',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Show only unread notifications',
                required=False
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """List user notifications with optional filtering."""
        queryset = self.get_queryset()
        
        # Filter for unread notifications if requested
        if request.query_params.get('unread_only', '').lower() == 'true':
            queryset = queryset.exclude(status=NotificationStatus.READ)
        
        # Apply filters and ordering
        queryset = self.filter_queryset(queryset)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Mark notifications as read",
        description="""
        Mark one or more notifications as read.
        
        **Request Body:**
        - `notification_ids`: List of notification IDs to mark as read
        
        **Response:**
        - `marked_read`: Number of notifications marked as read
        - `message`: Success message
        """,
        request=MarkNotificationReadSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "marked_read": {"type": "integer"},
                    "message": {"type": "string"}
                }
            },
            400: {"description": "Invalid notification IDs or validation errors"}
        }
    )
    @action(detail=False, methods=['post'])
    def mark_read(self, request):
        """Mark notifications as read."""
        serializer = MarkNotificationReadSerializer(
            data=request.data, 
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        notification_ids = serializer.validated_data['notification_ids']
        
        # Mark notifications as read
        updated_count = Notification.objects.filter(
            id__in=notification_ids,
            recipient=request.user,
        ).exclude(status=NotificationStatus.READ).update(
            status=NotificationStatus.READ,
            read_at=timezone.now()
        )
        
        return Response({
            'marked_read': updated_count,
            'message': f'Marked {updated_count} notifications as read'
        })
    
    @extend_schema(
        summary="Get notification statistics",
        description="""
        Get notification statistics for the authenticated user.
        
        **Returns:**
        - `total_notifications`: Total number of notifications
        - `unread_count`: Number of unread notifications
        - `by_type`: Count of notifications by type
        - `by_status`: Count of notifications by status
        """,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "total_notifications": {"type": "integer"},
                    "unread_count": {"type": "integer"},
                    "by_type": {"type": "object"},
                    "by_status": {"type": "object"}
                }
            }
        }
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get notification statistics for the user."""
        user_notifications = self.get_queryset()
        
        total_count = user_notifications.count()
        unread_count = user_notifications.exclude(status=NotificationStatus.READ).count()
        
        # Count by notification type
        type_counts = {}
        for notification_type, display_name in user_notifications.model.notification_type.field.choices:
            count = user_notifications.filter(notification_type=notification_type).count()
            if count > 0:
                type_counts[display_name] = count
        
        # Count by status
        status_counts = {}
        for notification_status, display_name in user_notifications.model.status.field.choices:
            count = user_notifications.filter(status=notification_status).count()
            if count > 0:
                status_counts[display_name] = count
        
        return Response({
            'total_notifications': total_count,
            'unread_count': unread_count,
            'by_type': type_counts,
            'by_status': status_counts,
        })


class FCMDeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for FCM device management.
    
    Allows users to:
    - Register devices for push notifications
    - View registered devices
    - Update device information
    - Remove devices
    """
    serializer_class = FCMDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return devices for the current user."""
        return FCMDevice.objects.filter(user=self.request.user)
    
    @extend_schema(
        summary="Register FCM device",
        description="""
        Register a device for push notifications.
        
        **Required Fields:**
        - `device_token`: FCM registration token from the client
        - `device_type`: Type of device (web, android, ios)
        
        **Optional Fields:**
        - `device_name`: Human-readable device name
        
        If a device with the same token already exists, it will be updated.
        """,
        responses={
            201: {"description": "Device registered successfully"},
            400: {"description": "Invalid device data"}
        }
    )
    def create(self, request, *args, **kwargs):
        """Register a new FCM device."""
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        summary="List user devices",
        description="Get all registered devices for the authenticated user."
    )
    def list(self, request, *args, **kwargs):
        """List user's registered devices."""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Deactivate device",
        description="Mark a device as inactive (stops sending push notifications)."
    )
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a device."""
        device = self.get_object()
        device.is_active = False
        device.save(update_fields=['is_active', 'updated_at'])
        
        return Response({
            'message': 'Device deactivated successfully'
        })
    
    @extend_schema(
        summary="Activate device",
        description="Mark a device as active (enables push notifications)."
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a device."""
        device = self.get_object()
        device.is_active = True
        device.save(update_fields=['is_active', 'updated_at'])
        
        return Response({
            'message': 'Device activated successfully'
        })


class NotificationPreferenceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for notification preferences.
    
    Allows users to:
    - View their notification preferences
    - Update notification preferences
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return preferences for the current user."""
        return NotificationPreference.objects.filter(user=self.request.user)
    
    def get_object(self):
        """Get or create notification preferences for the user."""
        preferences, created = NotificationPreference.objects.get_or_create(
            user=self.request.user,
            defaults={
                'email_transaction_created': True,
                'email_transaction_updated': True,
                'email_transaction_completed': True,
                'push_transaction_created': True,
                'push_transaction_updated': True,
                'push_transaction_completed': True,
                'admin_new_transactions': self.request.user.is_staff,
            }
        )
        return preferences
    
    @extend_schema(
        summary="Get notification preferences",
        description="Get notification preferences for the authenticated user."
    )
    def retrieve(self, request, *args, **kwargs):
        """Get user notification preferences."""
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Update notification preferences",
        description="""
        Update notification preferences for the authenticated user.
        
        **Available Preferences:**
        - Email notifications for transactions (created, updated, completed)
        - Push notifications for transactions (created, updated, completed)
        - Admin notifications for new transactions (admin users only)
        """,
        responses={
            200: {"description": "Preferences updated successfully"},
            400: {"description": "Invalid preference data"}
        }
    )
    def update(self, request, *args, **kwargs):
        """Update user notification preferences."""
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        """Partially update user notification preferences."""
        return super().partial_update(request, *args, **kwargs)
