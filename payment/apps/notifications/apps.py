from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'payment.apps.notifications'
    verbose_name = 'Notifications'
    
    def ready(self):
        """Import signal handlers when the app is ready."""
        import payment.apps.notifications.signals  # noqa
