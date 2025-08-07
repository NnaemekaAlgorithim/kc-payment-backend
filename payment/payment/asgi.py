"""
ASGI config for payment project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from payment.configurations import DEBUG

from django.core.asgi import get_asgi_application

if DEBUG:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payment.payment.settings.dev_settings")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payment.payment.settings.prod_settings")

application = get_asgi_application()
