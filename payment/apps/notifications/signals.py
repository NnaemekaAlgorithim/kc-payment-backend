import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from payment.apps.transactions.models import Transaction, TransactionStatus
from .services import notification_service

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transaction)
def handle_transaction_created(sender, instance, created, **kwargs):
    """
    Handle new transaction creation - notify admins.
    """
    if created:
        try:
            logger.info(f"New transaction created: {instance.reference_number} by {instance.user.email}")
            
            # Notify all admins about the new transaction
            notifications = notification_service.notify_admins_new_transaction(instance)
            
            logger.info(f"Sent {len(notifications)} notifications to admins for new transaction {instance.reference_number}")
            
        except Exception as e:
            logger.error(f"Error handling transaction creation notification: {str(e)}")


@receiver(pre_save, sender=Transaction)
def handle_transaction_status_change(sender, instance, **kwargs):
    """
    Handle transaction status changes - notify user about updates.
    This uses pre_save to capture the old status before it changes.
    """
    if instance.pk:  # Only for existing transactions
        try:
            # Get the current transaction from database
            old_transaction = Transaction.objects.get(pk=instance.pk)
            old_status = old_transaction.status
            new_status = instance.status
            
            # Only process if status actually changed
            if old_status != new_status:
                logger.info(f"Transaction {instance.reference_number} status changed: {old_status} -> {new_status}")
                
                # Determine the admin who made the change
                admin_user = getattr(instance, '_admin_user', None)
                if not admin_user and instance.processing_admin:
                    admin_user = instance.processing_admin
                elif not admin_user:
                    # Try to get the admin from processing_admin field
                    admin_user = User.objects.filter(is_staff=True, is_active=True).first()
                
                if admin_user:
                    # Map status to action
                    status_action_map = {
                        TransactionStatus.PROCESSING: 'processing',
                        TransactionStatus.COMPLETED: 'completed',
                        TransactionStatus.FAILED: 'failed',
                        TransactionStatus.CANCELLED: 'cancelled',
                    }
                    
                    action = status_action_map.get(new_status)
                    if action:
                        # Schedule notification after the transaction is saved
                        # We'll use a post_save signal for this
                        instance._notify_user_action = action
                        instance._notify_admin_user = admin_user
                        
        except Transaction.DoesNotExist:
            logger.warning(f"Transaction {instance.pk} not found in database during status change")
        except Exception as e:
            logger.error(f"Error handling transaction status change: {str(e)}")


@receiver(post_save, sender=Transaction)
def handle_transaction_updated(sender, instance, created, **kwargs):
    """
    Handle transaction updates - notify user if status changed.
    This runs after the transaction is saved.
    """
    if not created and hasattr(instance, '_notify_user_action'):
        try:
            action = instance._notify_user_action
            admin_user = instance._notify_admin_user
            
            logger.info(f"Notifying user about transaction {instance.reference_number} action: {action}")
            
            # Send notification to user
            notification = notification_service.notify_user_transaction_update(
                instance, action, admin_user
            )
            
            if notification:
                logger.info(f"Sent notification to {instance.user.email} for transaction {instance.reference_number}")
            else:
                logger.warning(f"Failed to send notification for transaction {instance.reference_number}")
            
            # Clean up the temporary attributes
            delattr(instance, '_notify_user_action')
            delattr(instance, '_notify_admin_user')
            
        except Exception as e:
            logger.error(f"Error handling transaction update notification: {str(e)}")


# Signal for FCM device management
@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    """
    Create default notification preferences for new users.
    """
    if created:
        try:
            from .models import NotificationPreference
            
            NotificationPreference.objects.get_or_create(
                user=instance,
                defaults={
                    'email_transaction_created': True,
                    'email_transaction_updated': True,
                    'email_transaction_completed': True,
                    'push_transaction_created': True,
                    'push_transaction_updated': True,
                    'push_transaction_completed': True,
                    'admin_new_transactions': instance.is_staff,
                }
            )
            
            logger.info(f"Created notification preferences for user: {instance.email}")
            
        except Exception as e:
            logger.error(f"Error creating notification preferences for {instance.email}: {str(e)}")
