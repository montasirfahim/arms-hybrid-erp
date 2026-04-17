from django.shortcuts import redirect
from django.http import JsonResponse
from functools import wraps
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import User

def login_required(view_func):
    """
    Decorator to require login for a view using JWT.
    Checks Authorization header first, then fallback to access_token cookie.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        else:
            token = request.COOKIES.get('access_token')

        if not token:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'success': False, 'message': 'Authentication required.'}, status=401)
            return redirect('login')

        try:
            # Verify and decode token
            decoded_token = AccessToken(token)
            user_id = decoded_token['user_id']
            
            # Optionally attach user to request
            # request.user_obj = User.objects.filter(pk=user_id).first()
            # if not request.user_obj:
            #     raise TokenError("User not found")
            
            return view_func(request, *args, **kwargs)
        except (TokenError, KeyError):
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'success': False, 'message': 'Invalid or expired token.'}, status=401)
            return redirect('login')
            
    return wrapper
