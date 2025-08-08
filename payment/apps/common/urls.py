from django.urls import path
from . import views

urlpatterns = [
    path('api-info/', views.api_root, name='api-root'),
    path('health/', views.health_check, name='health-check'),
]

app_name = 'common'
