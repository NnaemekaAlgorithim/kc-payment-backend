"""
WSGI config for payment project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from payment.configurations import DEBUG

from django.core.wsgi import get_wsgi_application

if DEBUG:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payment.payment.settings.dev_settings")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payment.payment.settings.prod_settings")

application = get_wsgi_application()
