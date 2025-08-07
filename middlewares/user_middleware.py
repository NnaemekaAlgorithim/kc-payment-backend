import threading
from django.contrib.auth import get_user_model

_user_local = threading.local()
User = get_user_model()


class CurrentUserMiddleware:
    """
    Middleware to store the current user in thread-local storage.
    This allows access to the current user from anywhere in the application.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store the current user in thread-local storage
        _user_local.user = getattr(request, 'user', None)
        
        response = self.get_response(request)
        
        # Clean up thread-local storage
        if hasattr(_user_local, 'user'):
            del _user_local.user
            
        return response


def get_current_user():
    """
    Get the current user from thread-local storage.
    Returns None if no user is available.
    """
    return getattr(_user_local, 'user', None)
