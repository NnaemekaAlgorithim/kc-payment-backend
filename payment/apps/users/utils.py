import random
import string
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


class OTPManager:
    """Manager for OTP operations using Redis cache."""
    
    @staticmethod
    def generate_otp(length=6):
        """Generate a random OTP."""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def store_otp(email, otp, purpose, timeout=600):
        """
        Store OTP in Redis cache with a timeout (default 10 minutes).
        
        Args:
            email: User's email
            otp: Generated OTP
            purpose: Purpose of OTP (registration, password_reset)
            timeout: Timeout in seconds (default 600 = 10 minutes)
        """
        cache_key = f"otp_{purpose}_{email}"
        cache.set(cache_key, otp, timeout)
        return cache_key
    
    @staticmethod
    def verify_otp(email, otp, purpose):
        """
        Verify OTP from Redis cache.
        
        Args:
            email: User's email
            otp: OTP to verify
            purpose: Purpose of OTP (registration, password_reset)
        
        Returns:
            bool: True if OTP is valid, False otherwise
        """
        cache_key = f"otp_{purpose}_{email}"
        stored_otp = cache.get(cache_key)
        
        if stored_otp and stored_otp == otp:
            # Remove OTP after successful verification
            cache.delete(cache_key)
            return True
        return False
    
    @staticmethod
    def get_remaining_time(email, purpose):
        """
        Get remaining time for OTP validity.
        
        Args:
            email: User's email
            purpose: Purpose of OTP
        
        Returns:
            int: Remaining time in seconds, 0 if expired or not found
        """
        cache_key = f"otp_{purpose}_{email}"
        return cache.ttl(cache_key) if cache.has_key(cache_key) else 0


class EmailService:
    """Service for sending emails."""
    
    @staticmethod
    def send_activation_email(user, otp):
        """Send account activation email."""
        subject = 'Activate Your Account'
        
        # Render HTML template
        html_message = render_to_string('emails/activation_email.html', {
            'user': user,
            'otp': otp,
            'site_name': 'Payment Platform'
        })
        
        # Create plain text version
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    
    @staticmethod
    def send_password_reset_email(user, otp):
        """Send password reset email."""
        subject = 'Reset Your Password'
        
        # Render HTML template
        html_message = render_to_string('emails/password_reset_email.html', {
            'user': user,
            'otp': otp,
            'site_name': 'Payment Platform'
        })
        
        # Create plain text version
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
    
    @staticmethod
    def send_welcome_email(user):
        """Send welcome email after successful activation."""
        subject = 'Welcome to Payment Platform!'
        
        # Render HTML template
        html_message = render_to_string('emails/welcome_email.html', {
            'user': user,
            'site_name': 'Payment Platform'
        })
        
        # Create plain text version
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
