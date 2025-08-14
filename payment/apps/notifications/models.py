from django.db import models
from django.contrib.auth import get_user_model
from payment.apps.common.models import BaseModel

User = get_user_model()


class NotificationType(models.TextChoices):
    """Notification type choices."""
    TRANSACTION_CREATED = 'transaction_created', 'Transaction Created'
    TRANSACTION_UPDATED = 'transaction_updated', 'Transaction Updated'
    TRANSACTION_PROCESSING = 'transaction_processing', 'Transaction Processing'
    TRANSACTION_COMPLETED = 'transaction_completed', 'Transaction Completed'
    TRANSACTION_FAILED = 'transaction_failed', 'Transaction Failed'
    TRANSACTION_CANCELLED = 'transaction_cancelled', 'Transaction Cancelled'


class NotificationStatus(models.TextChoices):
    """Notification status choices."""
    PENDING = 'pending', 'Pending'
    SENT = 'sent', 'Sent'
    DELIVERED = 'delivered', 'Delivered'
    FAILED = 'failed', 'Failed'
    READ = 'read', 'Read'


class Notification(BaseModel):
    """
    Model for storing notifications for users and admins.
    """
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who will receive this notification"
    )
    
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
        help_text="Type of notification"
    )
    
    title = models.CharField(
        max_length=200,
        help_text="Notification title"
    )
    
    message = models.TextField(
        help_text="Notification message content"
    )
    
    # Transaction reference
    transaction_id = models.CharField(
        max_length=26,
        null=True,
        blank=True,
        help_text="Related transaction ID (string-based primary key)"
    )
    
    transaction_reference = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Related transaction reference number"
    )
    
    # Additional data as JSON
    extra_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional notification data"
    )
    
    # Notification status
    status = models.CharField(
        max_length=20,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
        help_text="Notification delivery status"
    )
    
    # Timestamps
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was sent"
    )
    
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was delivered"
    )
    
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When notification was read by user"
    )
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['notification_type', 'created_at']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['transaction_reference']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.recipient.email}"
    
    @property
    def is_read(self):
        """Check if notification has been read."""
        return self.status == NotificationStatus.READ
    
    def mark_as_read(self):
        """Mark notification as read."""
        if self.status != NotificationStatus.READ:
            self.status = NotificationStatus.READ
            self.read_at = models.functions.Now()
            self.save(update_fields=['status', 'read_at', 'updated_at'])


class FCMDevice(BaseModel):
    """
    Model for storing user FCM device tokens for push notifications.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fcm_devices',
        help_text="User who owns this device"
    )
    
    device_token = models.TextField(
        unique=True,
        help_text="FCM device registration token"
    )
    
    device_type = models.CharField(
        max_length=10,
        choices=[
            ('web', 'Web'),
            ('android', 'Android'),
            ('ios', 'iOS'),
        ],
        help_text="Type of device"
    )
    
    device_name = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Device name or identifier"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether device is active for notifications"
    )
    
    last_used = models.DateTimeField(
        auto_now=True,
        help_text="Last time device was used"
    )
    
    class Meta:
        db_table = 'fcm_devices'
        ordering = ['-last_used']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.device_type}"


class NotificationPreference(BaseModel):
    """
    Model for storing user notification preferences.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
        help_text="User preferences"
    )
    
    # Email notifications
    email_transaction_created = models.BooleanField(
        default=True,
        help_text="Email when transaction is created"
    )
    
    email_transaction_updated = models.BooleanField(
        default=True,
        help_text="Email when transaction is updated"
    )
    
    email_transaction_completed = models.BooleanField(
        default=True,
        help_text="Email when transaction is completed"
    )
    
    # Push notifications
    push_transaction_created = models.BooleanField(
        default=True,
        help_text="Push notification when transaction is created"
    )
    
    push_transaction_updated = models.BooleanField(
        default=True,
        help_text="Push notification when transaction is updated"
    )
    
    push_transaction_completed = models.BooleanField(
        default=True,
        help_text="Push notification when transaction is completed"
    )
    
    # Admin-specific preferences (only for staff users)
    admin_new_transactions = models.BooleanField(
        default=True,
        help_text="Notify admin of new transactions (admin only)"
    )
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.email}"
