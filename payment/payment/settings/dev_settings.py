from .base_settings import *
import os

# Override DEBUG to ensure it's True in development
DEBUG = True

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
print("Using local SQLite as database and email will be seen on the console.")

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Use console for development

# Override any database configuration from base_settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Ensure we're not using any dummy database configuration
DATABASE_URL = None
