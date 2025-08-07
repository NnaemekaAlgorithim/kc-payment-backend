from decouple import config, Csv

# Basic settings
BASE_PREFIX = config('BASE_PREFIX', default='')
DEBUG = config('DEBUG', default=True, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# Email settings
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@payment.com')

# Social Authentication
ENABLE_SOCIAL_AUTH = config('ENABLE_SOCIAL_AUTH', default=False, cast=bool)
SOCIAL_AUTH_FACEBOOK_SCOPE = config('SOCIAL_AUTH_FACEBOOK_SCOPE', default='email')
SOCIAL_AUTH_FACEBOOK_SECRET = config('SOCIAL_AUTH_FACEBOOK_SECRET', default='')
SOCIAL_AUTH_FACEBOOK_KEY = config('SOCIAL_AUTH_FACEBOOK_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', default='')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = config('SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE', default='openid email profile')
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')

# Cloudinary settings
CLOUDINARY_CLOUD_NAME = config('CLOUDINARY_CLOUD_NAME', default='')
CLOUDINARY_API_KEY = config('CLOUDINARY_API_KEY', default='')
CLOUDINARY_API_SECRET = config('CLOUDINARY_API_SECRET', default='')

# Database settings
DB_HOST_NAME = config('DB_HOST_NAME', default='localhost')
DB_PORT = config('DB_PORT', default=5432, cast=int)
DB_NAME = config('DB_NAME', default='payment_db')
DB_USER_NAME = config('DB_USER_NAME', default='postgres')
DB_PASSWORD = config('DB_PASSWORD', default='')
DATABASE_URL = config('DATABASE_URL', default=f'postgresql://{DB_USER_NAME}:{DB_PASSWORD}@{DB_HOST_NAME}:{DB_PORT}/{DB_NAME}')

# Redis settings
REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')

# Stripe settings
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Celery settings
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')

# Security settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = config('SECURE_PROXY_SSL_HEADER', default=False, cast=bool)
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=False, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=False, cast=bool)

# Logging
LOG_LEVEL = config('LOG_LEVEL', default='INFO')
