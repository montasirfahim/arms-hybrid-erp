from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from .models import User

def get_user_from_jwt(request):
    """
    Helper to extract user from JWT.

    Checks Authorization header first, then COOKIES.
    """
    token = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    else:
        token = request.COOKIES.get('access_token')

    if not token:
        return None

    try:
        decoded_token = AccessToken(token)
        user_id = decoded_token['user_id']
        return User.objects.filter(pk=user_id).first()
    except (TokenError, KeyError):
        return None

def get_password_reset_email_body(user_name, otp):
    return f"""
    <html>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">

                <div style="background-color: #1a56db; padding: 25px; text-align: center;">
                    <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 600;">Password Reset Request</h2>
                </div>

                <div style="padding: 40px 30px;">
                    <p style="font-size: 16px; margin-top: 0;">Hello <strong>{user_name}</strong>,</p>
                    <p style="color: #4b5563;">We received a request to reset your password for your ARMS account. Use the verification code below to proceed:</p>

                    <div style="text-align: center; margin: 35px 0;">
                        <div style="display: inline-block; font-family: 'Courier New', Courier, monospace; font-size: 36px; font-weight: bold; letter-spacing: 6px; color: #1a56db; background: #f0f4ff; padding: 15px 30px; border-radius: 8px; border: 2px dashed #1a56db;">
                            {otp}
                        </div>
                    </div>

                    <p style="font-size: 14px; color: #6b7280; text-align: center; margin-bottom: 0;">
                        This OTP is valid for <strong>3 minutes</strong>.<br>
                        If you did not request this, you can safely ignore this email.
                    </p>
                </div>

                <div style="background-color: #f9fafb; padding: 25px; text-align: center; border-top: 1px solid #e0e0e0;">
                    <p style="font-size: 13px; color: #6b7280; margin: 0; font-weight: 500;">
                        Powered by <strong>ARMS</strong>
                    </p>
                    <p style="font-size: 12px; color: #9ca3af; margin: 4px 0 0;">
                        Department of ICT, MBSTU
                    </p>
                    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 15px auto; width: 50px;">
                    <p style="font-size: 11px; color: #d1d5db; margin: 0;">
                        This is an automated security notification. Please do not reply.
                    </p>
                </div>
            </div>
        </body>
    </html>
    """