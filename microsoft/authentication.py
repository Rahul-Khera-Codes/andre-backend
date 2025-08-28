# authentication.py
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.utils.translation import gettext_lazy as _

from .utils.auth import verify_access_token 
from .models import MicrosoftConnectedAccounts


class MicrosoftOAuthAuthentication(BaseAuthentication):
    is_authenticated: bool = False
    
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]

        try:
            account = verify_access_token(token)
        except Exception as e:
            raise exceptions.AuthenticationFailed(_("Invalid or expired token"))

        if not account or not isinstance(account, MicrosoftConnectedAccounts):
            raise exceptions.AuthenticationFailed(_("User not found"))
        
        return (account, None)
