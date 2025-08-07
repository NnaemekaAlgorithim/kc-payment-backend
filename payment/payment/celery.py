import os
from celery import Celery
from payment.configurations import DEBUG

# Set the default Django settings module
if DEBUG:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment.payment.settings.dev_settings')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment.payment.settings.prod_settings')

app = Celery('payment')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
