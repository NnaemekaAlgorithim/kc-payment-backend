import json
import logging
from typing import List, Dict, Optional
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

import requests

from .models import Notification, FCMDevice, NotificationStatus, NotificationType

User = get_user_model()
logger = logging.getLogger(__name__)


class FCMNotificationService:
    """
    Service for sending Firebase Cloud Messaging push notifications.
    """
    
    def __init__(self):
        self.server_key = getattr(settings, 'FCM_SERVER_KEY', None)
        self.fcm_url = 'https://fcm.googleapis.com/fcm/send'
    
    def send_to_device(self, device_token: str, title: str, body: str, 
                      data: Optional[Dict] = None) -> bool:
        """
        Send push notification to a specific device.
        
        Args:
            device_token: FCM device registration token
            title: Notification title
            body: Notification body
            data: Additional data to send with notification
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.server_key:
            logger.error("FCM_SERVER_KEY not configured in settings")
            return False
        
        headers = {
            'Authorization': f'key={self.server_key}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'to': device_token,
            'notification': {
                'title': title,
                'body': body,
                'click_action': 'FLUTTER_NOTIFICATION_CLICK',  # For mobile apps
            },
            'data': data or {}
        }
        
        try:
            response = requests.post(
                self.fcm_url,
                headers=headers,
                data=json.dumps(payload),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success', 0) > 0:
                    logger.info(f"FCM notification sent successfully to {device_token[:20]}...")
                    return True
                else:
                    logger.error(f"FCM notification failed: {result}")
                    return False
            else:
                logger.error(f"FCM request failed with status {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending FCM notification: {str(e)}")
            return False
    
    def send_to_user(self, user: User, title: str, body: str, 
                     data: Optional[Dict] = None) -> int:
        """
        Send push notification to all active devices of a user.
        
        Args:
            user: User to send notification to
            title: Notification title
            body: Notification body
            data: Additional data to send with notification
            
        Returns:
            int: Number of successful sends
        """
        devices = FCMDevice.objects.filter(user=user, is_active=True)
        successful_sends = 0
        
        for device in devices:
            if self.send_to_device(device.device_token, title, body, data):
                successful_sends += 1
            else:
                # Mark inactive devices
                device.is_active = False
                device.save(update_fields=['is_active', 'updated_at'])
        
        return successful_sends
    
    def send_to_admins(self, title: str, body: str, data: Optional[Dict] = None) -> int:
        """
        Send push notification to all admin users.
        
        Args:
            title: Notification title
            body: Notification body
            data: Additional data to send with notification
            
        Returns:
            int: Number of successful sends
        """
        admin_users = User.objects.filter(is_staff=True, is_active=True)
        total_sends = 0
        
        for admin in admin_users:
            # Check admin preferences
            prefs = getattr(admin, 'notification_preferences', None)
            if prefs and not prefs.admin_new_transactions:
                continue
                
            total_sends += self.send_to_user(admin, title, body, data)
        
        return total_sends


class NotificationService:
    """
    Main notification service for handling all notification types.
    """
    
    def __init__(self):
        self.fcm_service = FCMNotificationService()
    
    def create_notification(self, recipient: User, notification_type: str,
                          title: str, message: str, transaction_id: Optional[int] = None,
                          transaction_reference: Optional[str] = None,
                          extra_data: Optional[Dict] = None) -> Notification:
        """
        Create a new notification record.
        """
        notification = Notification.objects.create(
            recipient=recipient,
            notification_type=notification_type,
            title=title,
            message=message,
            transaction_id=transaction_id,
            transaction_reference=transaction_reference,
            extra_data=extra_data or {}
        )
        
        logger.info(f"Created notification: {title} for {recipient.email}")
        return notification
    
    def send_push_notification(self, notification: Notification) -> bool:
        """
        Send push notification via FCM.
        """
        try:
            data = {
                'notification_id': str(notification.id),
                'notification_type': notification.notification_type,
                'transaction_id': str(notification.transaction_id) if notification.transaction_id else None,
                'transaction_reference': notification.transaction_reference,
            }
            
            success_count = self.fcm_service.send_to_user(
                notification.recipient,
                notification.title,
                notification.message,
                data
            )
            
            if success_count > 0:
                notification.status = NotificationStatus.SENT
                notification.sent_at = timezone.now()
                notification.save(update_fields=['status', 'sent_at', 'updated_at'])
                return True
            else:
                notification.status = NotificationStatus.FAILED
                notification.save(update_fields=['status', 'updated_at'])
                return False
                
        except Exception as e:
            logger.error(f"Error sending push notification {notification.id}: {str(e)}")
            notification.status = NotificationStatus.FAILED
            notification.save(update_fields=['status', 'updated_at'])
            return False
    
    def notify_admins_new_transaction(self, transaction) -> List[Notification]:
        """
        Notify all admins about a new transaction.
        """
        title = "New Transaction Created"
        message = f"Transaction #{transaction.reference_number} created by {transaction.user.email}"
        
        admin_users = User.objects.filter(is_staff=True, is_active=True)
        notifications = []
        
        for admin in admin_users:
            # Check admin preferences
            prefs = getattr(admin, 'notification_preferences', None)
            if prefs and not prefs.admin_new_transactions:
                continue
            
            # Create notification record
            notification = self.create_notification(
                recipient=admin,
                notification_type=NotificationType.TRANSACTION_CREATED,
                title=title,
                message=message,
                transaction_id=transaction.id,
                transaction_reference=transaction.reference_number,
                extra_data={
                    'user_email': transaction.user.email,
                    'amount': str(transaction.amount),
                    'currency': transaction.currency,
                }
            )
            
            # Send push notification
            self.send_push_notification(notification)
            notifications.append(notification)
        
        # Also send to all admins via FCM
        data = {
            'transaction_id': str(transaction.id),
            'transaction_reference': transaction.reference_number,
            'user_email': transaction.user.email,
        }
        
        self.fcm_service.send_to_admins(title, message, data)
        
        return notifications
    
    def notify_user_transaction_update(self, transaction, action: str, admin_user: User) -> Optional[Notification]:
        """
        Notify user about transaction update.
        """
        action_messages = {
            'processing': f"Your transaction #{transaction.reference_number} is now being processed",
            'completed': f"Your transaction #{transaction.reference_number} has been completed",
            'failed': f"Your transaction #{transaction.reference_number} has failed",
            'cancelled': f"Your transaction #{transaction.reference_number} has been cancelled",
        }
        
        title_map = {
            'processing': 'Transaction Processing',
            'completed': 'Transaction Completed',
            'failed': 'Transaction Failed',
            'cancelled': 'Transaction Cancelled',
        }
        
        type_map = {
            'processing': NotificationType.TRANSACTION_PROCESSING,
            'completed': NotificationType.TRANSACTION_COMPLETED,
            'failed': NotificationType.TRANSACTION_FAILED,
            'cancelled': NotificationType.TRANSACTION_CANCELLED,
        }
        
        title = title_map.get(action, 'Transaction Updated')
        message = action_messages.get(action, f"Your transaction #{transaction.reference_number} has been updated")
        notification_type = type_map.get(action, NotificationType.TRANSACTION_UPDATED)
        
        # Check user preferences
        user_prefs = getattr(transaction.user, 'notification_preferences', None)
        
        # Create notification record
        notification = self.create_notification(
            recipient=transaction.user,
            notification_type=notification_type,
            title=title,
            message=message,
            transaction_id=transaction.id,
            transaction_reference=transaction.reference_number,
            extra_data={
                'action': action,
                'admin_email': admin_user.email,
                'admin_name': f"{admin_user.first_name} {admin_user.last_name}".strip() or admin_user.email,
            }
        )
        
        # Send push notification if user has enabled it
        if (not user_prefs or 
            (action == 'completed' and user_prefs.push_transaction_completed) or
            (action in ['processing', 'failed', 'cancelled'] and user_prefs.push_transaction_updated)):
            
            self.send_push_notification(notification)
        
        return notification
    
    def get_user_notifications(self, user: User, unread_only: bool = False) -> List[Notification]:
        """
        Get notifications for a user.
        """
        queryset = Notification.objects.filter(recipient=user)
        
        if unread_only:
            queryset = queryset.exclude(status=NotificationStatus.READ)
        
        return list(queryset.order_by('-created_at'))
    
    def mark_notification_read(self, notification_id: int, user: User) -> bool:
        """
        Mark a notification as read.
        """
        try:
            notification = Notification.objects.get(id=notification_id, recipient=user)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False


# Global instance
notification_service = NotificationService()
