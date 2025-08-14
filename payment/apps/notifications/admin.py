from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Notification, FCMDevice, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'recipient_email', 'notification_type', 'status', 
        'transaction_link', 'created_at'
    ]
    list_filter = [
        'notification_type', 'status', 'created_at', 'sent_at'
    ]
    search_fields = [
        'title', 'message', 'recipient__email', 'transaction_reference'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'sent_at', 'delivered_at'
    ]
    raw_id_fields = ['recipient']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'recipient', 'notification_type', 'title', 'message'
            )
        }),
        ('Transaction Details', {
            'fields': (
                'transaction_id', 'transaction_reference', 'extra_data'
            ),
            'classes': ('collapse',)
        }),
        ('Status & Timestamps', {
            'fields': (
                'status', 'sent_at', 'delivered_at', 'read_at'
            )
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def recipient_email(self, obj):
        """Display recipient email."""
        return obj.recipient.email
    recipient_email.short_description = 'Recipient'
    recipient_email.admin_order_field = 'recipient__email'
    
    def transaction_link(self, obj):
        """Create link to transaction if available."""
        if obj.transaction_id:
            return format_html(
                '<a href="{}">#{}</a>',
                reverse('admin:transactions_transaction_change', args=[obj.transaction_id]),
                obj.transaction_reference or obj.transaction_id
            )
        return '-'
    transaction_link.short_description = 'Transaction'
    transaction_link.admin_order_field = 'transaction_id'
    
    actions = ['mark_as_read', 'mark_as_sent']
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        updated = 0
        for notification in queryset:
            if not notification.is_read:
                notification.mark_as_read()
                updated += 1
        
        self.message_user(
            request, 
            f'{updated} notification(s) marked as read.'
        )
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    def mark_as_sent(self, request, queryset):
        """Mark selected notifications as sent."""
        from .models import NotificationStatus
        from django.utils import timezone
        
        updated = queryset.exclude(status=NotificationStatus.SENT).update(
            status=NotificationStatus.SENT,
            sent_at=timezone.now()
        )
        
        self.message_user(
            request,
            f'{updated} notification(s) marked as sent.'
        )
    mark_as_sent.short_description = 'Mark selected notifications as sent'


@admin.register(FCMDevice)
class FCMDeviceAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user_email', 'device_type', 'device_name', 
        'is_active', 'last_used', 'created_at'
    ]
    list_filter = [
        'device_type', 'is_active', 'created_at', 'last_used'
    ]
    search_fields = [
        'user__email', 'device_name', 'device_token'
    ]
    readonly_fields = [
        'id', 'device_token_display', 'created_at', 'updated_at', 'last_used'
    ]
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Device Information', {
            'fields': (
                'user', 'device_type', 'device_name', 'is_active'
            )
        }),
        ('Token', {
            'fields': ('device_token_display', 'device_token'),
            'description': 'The FCM registration token for this device'
        }),
        ('Timestamps', {
            'fields': ('last_used', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def device_token_display(self, obj):
        """Display truncated device token."""
        if obj.device_token:
            return f"{obj.device_token[:20]}...{obj.device_token[-10:]}"
        return '-'
    device_token_display.short_description = 'Device Token (truncated)'
    
    actions = ['activate_devices', 'deactivate_devices']
    
    def activate_devices(self, request, queryset):
        """Activate selected devices."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} device(s) activated.'
        )
    activate_devices.short_description = 'Activate selected devices'
    
    def deactivate_devices(self, request, queryset):
        """Deactivate selected devices."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} device(s) deactivated.'
        )
    deactivate_devices.short_description = 'Deactivate selected devices'


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'email_enabled', 'push_enabled', 
        'admin_notifications', 'updated_at'
    ]
    list_filter = [
        'email_transaction_created', 'push_transaction_created',
        'admin_new_transactions', 'created_at'
    ]
    search_fields = ['user__email']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Email Notifications', {
            'fields': (
                'email_transaction_created',
                'email_transaction_updated',
                'email_transaction_completed'
            )
        }),
        ('Push Notifications', {
            'fields': (
                'push_transaction_created',
                'push_transaction_updated',
                'push_transaction_completed'
            )
        }),
        ('Admin Preferences', {
            'fields': ('admin_new_transactions',),
            'description': 'Settings for admin users only'
        })
    )
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'User'
    user_email.admin_order_field = 'user__email'
    
    def email_enabled(self, obj):
        """Check if any email notifications are enabled."""
        return any([
            obj.email_transaction_created,
            obj.email_transaction_updated,
            obj.email_transaction_completed
        ])
    email_enabled.boolean = True
    email_enabled.short_description = 'Email Enabled'
    
    def push_enabled(self, obj):
        """Check if any push notifications are enabled."""
        return any([
            obj.push_transaction_created,
            obj.push_transaction_updated,
            obj.push_transaction_completed
        ])
    push_enabled.boolean = True
    push_enabled.short_description = 'Push Enabled'
    
    def admin_notifications(self, obj):
        """Display admin notification preference."""
        return obj.admin_new_transactions
    admin_notifications.boolean = True
    admin_notifications.short_description = 'Admin Notifications'
