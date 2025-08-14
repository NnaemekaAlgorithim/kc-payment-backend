from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Notification, FCMDevice, NotificationPreference

User = get_user_model()


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications.
    """
    recipient_email = serializers.EmailField(source='recipient.email', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient_email',
            'notification_type',
            'notification_type_display',
            'title',
            'message',
            'transaction_id',
            'transaction_reference',
            'extra_data',
            'status',
            'status_display',
            'sent_at',
            'delivered_at',
            'read_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'recipient_email', 'notification_type_display', 
            'status_display', 'sent_at', 'delivered_at', 'read_at',
            'created_at', 'updated_at'
        ]


class FCMDeviceSerializer(serializers.ModelSerializer):
    """
    Serializer for FCM device registration.
    """
    
    class Meta:
        model = FCMDevice
        fields = [
            'id',
            'device_token',
            'device_type',
            'device_name',
            'is_active',
            'last_used',
            'created_at',
        ]
        read_only_fields = ['id', 'last_used', 'created_at']
    
    def create(self, validated_data):
        """Create or update FCM device."""
        user = self.context['request'].user
        device_token = validated_data['device_token']
        
        # Check if device already exists for this user
        device, created = FCMDevice.objects.update_or_create(
            device_token=device_token,
            defaults={
                'user': user,
                'device_type': validated_data.get('device_type', 'web'),
                'device_name': validated_data.get('device_name', ''),
                'is_active': True,
            }
        )
        
        return device


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """
    Serializer for notification preferences.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id',
            'user_email',
            'email_transaction_created',
            'email_transaction_updated',
            'email_transaction_completed',
            'push_transaction_created',
            'push_transaction_updated',
            'push_transaction_completed',
            'admin_new_transactions',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user_email', 'created_at', 'updated_at']
    
    def validate_admin_new_transactions(self, value):
        """Only staff users can enable admin notifications."""
        user = self.context['request'].user
        if value and not user.is_staff:
            raise serializers.ValidationError(
                "Only admin users can enable admin notifications."
            )
        return value


class MarkNotificationReadSerializer(serializers.Serializer):
    """
    Serializer for marking notifications as read.
    """
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of notification IDs to mark as read"
    )
    
    def validate_notification_ids(self, value):
        """Validate that all notifications belong to the current user."""
        user = self.context['request'].user
        
        # Check if all notifications exist and belong to the user
        existing_notifications = Notification.objects.filter(
            id__in=value,
            recipient=user
        ).values_list('id', flat=True)
        
        missing_ids = set(value) - set(existing_notifications)
        if missing_ids:
            raise serializers.ValidationError(
                f"Notifications with IDs {list(missing_ids)} not found or don't belong to you."
            )
        
        return value
