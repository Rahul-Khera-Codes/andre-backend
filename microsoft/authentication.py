import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from traceback import format_exc

from asgiref.sync import sync_to_async
from channels.middleware import BaseMiddleware
from channels.exceptions import DenyConnection
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError
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


async def async_verify_access_token(token_str: str):
    loop = asyncio.get_running_loop()
    results = await loop.run_in_executor(
        ThreadPoolExecutor(),
        verify_access_token,
        token_str
    )
    return results

class CustomJWTMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)
        print("Websocket CustomMiddleware __init__:", inner)
    
    async def check_header(self, scope):
        auth_header = None
        for t in scope['headers']:
            key, value = t[0], t[1]
            if key == b'authorization':
                auth_header = value
        
        token = None
        if auth_header:
            try:
                token_name, token = auth_header.decode('utf-8').split()
                if token_name.lower() != "bearer":
                    raise ValueError("Invalid auth scheme")
            except Exception:
                raise DenyConnection("Invalid Authorization header format")
    
        if not token:
            raise DenyConnection("Missing jwt token")
        return token
    
    
    async def check_query_string(self, scope):
        qs_dict =  dict([x.split("=") for x in scope['query_string'].decode('utf-8').split("&")])
        token = qs_dict.get("token")
        if not token:
            raise DenyConnection("Missing jwt token")
        return token
        
        
    async def __call__(self, scope, receive, send):
        
        try:
            # print("Websocket CustomMiddleware __call__ ->", "Scope:", scope, "Receive:", receive, "Send:", send)
            token = await self.check_query_string(scope)
            account = None    
            try:
                account = await async_verify_access_token(token)
            except TokenError as e:
                raise DenyConnection("Invalid auth token")
            
            if not account:
                raise DenyConnection("User not found")
                
            scope['account'] = account
            return await super().__call__(scope, receive, send)
            
        except Exception as e:
            print(format_exc())
            print("\nReason: ", str(e), "\n")
            await send({
                "type": "websocket.close",
                "code": 4003,
                "reason": str(e)
            })
            return 
            
        