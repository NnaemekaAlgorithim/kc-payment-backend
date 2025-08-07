#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Check for DEBUG environment variable first, then import configurations
    debug_env = os.environ.get('DEBUG', '').lower() in ('true', '1', 'yes', 'on')
    
    if debug_env:
        # Force development settings when DEBUG=True in environment
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment.payment.settings.dev_settings')
    else:
        # Import configurations to check DEBUG setting from .env file
        try:
            from payment.configurations import DEBUG
            if DEBUG:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment.payment.settings.dev_settings')
            else:
                os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment.payment.settings.prod_settings')
        except ImportError:
            # Fallback to development settings if import fails
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment.payment.settings.dev_settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
