import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class BaseModel(models.Model):
    """
    Abstract base model with common fields for all models.
    """
    id = models.CharField(max_length=26, primary_key=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        if not self.id:
            # Generate a unique ID (you can use ulid or uuid)
            import time
            import random
            import string
            timestamp = int(time.time() * 1000)
            random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            self.id = f"{timestamp:013d}{random_part}"
        super().save(*args, **kwargs)


class TimestampMixin(models.Model):
    """
    Mixin to add timestamp fields to models.
    """
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when the record was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp when the record was last updated")
    
    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Mixin to add soft delete functionality to models.
    """
    is_deleted = models.BooleanField(default=False, help_text="Indicates if the record is soft deleted")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when the record was soft deleted")
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        """Soft delete the instance."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def restore(self):
        """Restore a soft deleted instance."""
        self.is_deleted = False
        self.deleted_at = None
        self.save()


class StatusChoices(models.TextChoices):
    """
    Common status choices for models.
    """
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    PENDING = 'pending', 'Pending'
    SUSPENDED = 'suspended', 'Suspended'


# Example model using the mixins
class CommonSettings(BaseModel, TimestampMixin, SoftDeleteMixin):
    """
    Model to store application-wide settings.
    """
    key = models.CharField(max_length=255, unique=True, help_text="Setting key")
    value = models.TextField(help_text="Setting value")
    description = models.TextField(blank=True, help_text="Description of the setting")
    is_public = models.BooleanField(default=False, help_text="Whether this setting is public")
    
    class Meta:
        db_table = 'payment_common_settings'
        verbose_name = 'Common Setting'
        verbose_name_plural = 'Common Settings'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}..."
