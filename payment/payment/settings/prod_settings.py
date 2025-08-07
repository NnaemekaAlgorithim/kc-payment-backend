from .base_settings import *
import dj_database_url


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

EMAIL_BACKEND = EMAIL_BACKEND

DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }
