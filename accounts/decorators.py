from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps


def login_required(view_func):
    """
    Decorator to require login for a view.
    Redirects to login page if user is not authenticated.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user has JWT token in session or is authenticated via Django
        if not request.session.get('is_authenticated') and not request.user.is_authenticated:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper
