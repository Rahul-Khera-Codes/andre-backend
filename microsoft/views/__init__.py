import os
from tracemalloc import Filter

from django.shortcuts import redirect
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.exceptions import (
    ExpiredTokenError,
    InvalidToken,
    TokenError
)
from rest_framework_simplejwt.tokens import (
    AccessToken,
    RefreshToken
)

from ..models import MicrosoftConnectedAccounts
from ..utils import generate_access_token, get_refresh_token, get_user_info
from ..tasks import new_user_mail_sync
from ..serializers import MicrosoftConnectAccountSerializer


def get_tokens_for_user(user: MicrosoftConnectedAccounts):
    refresh = RefreshToken.for_user(user)
    refresh['id'] = user.id
    refresh['microsoft_id'] = user.microsoft_id
    refresh['display_name'] = user.display_name

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        "id": user.id,
        "microsoft_id": user.microsoft_id,
        "display_name": user.display_name
    }
    

def verify_access_token(token_str):
    # Decode and verify token
    access_token = AccessToken(token_str)
    microsoft_id = access_token['microsoft_id']  # default claim
    user = MicrosoftConnectedAccounts.objects.get(microsoft_id=microsoft_id)
    return user
    
    
class MicrosoftConnectVerify(APIView):
    def get(self, request):
        code = request.GET.get('code')
        print(code)
        
        status_code, response = generate_access_token(code)
        print("1", status_code)
        if status_code != 200:
            return redirect(f"{os.getenv("FRONTEND_URL")}?response=error", status=status.HTTP_302_FOUND)
        
        access_token = response.get('access_token')
        refresh_token = response.get('refresh_token')
        print("Access_token:", access_token)
        
        status_code, user_data = get_user_info(access_token)
        
        if status_code !=200:
            return redirect(f"{os.getenv("FRONTEND_URL")}?response=error", status=status.HTTP_302_FOUND)

        user_principal_name = user_data.get('userPrincipalName')
        microsoft_id = user_data.get('id')
        display_name = user_data.get('displayName')
        surname = user_data.get('surname')
        given_name = user_data.get('givenName')
        mail = user_data.get('mail')
        
        try:    
            account = MicrosoftConnectedAccounts.objects.filter(microsoft_id=microsoft_id).first()
            
            if account:
                account.access_token = access_token
                account.refresh_token = refresh_token
                account.save()
                            
            if not account:
                account = MicrosoftConnectedAccounts.objects.create(
                    access_token=access_token, 
                    display_name=display_name, 
                    given_name=given_name, 
                    mail_id=mail,
                    microsoft_id=microsoft_id, 
                    refresh_token=refresh_token,
                    surname=surname,
                    user_principal_name=user_principal_name,
                )
            new_user_mail_sync.delay(access_token, account.id)
            
            microsoft_id = account.microsoft_id
            
            
        except Exception as e:
            print(e)
            return redirect(f"{os.getenv("FRONTEND_URL")}/dashboard?response=error", status=status.HTTP_302_FOUND)
        
        return redirect(f"{os.getenv("FRONTEND_URL")}/dashboard?response=success&mid={microsoft_id}", status=status.HTTP_302_FOUND)
    
    
class GetConnectedAccounts(APIView):    
    def get(self, request):
        microsoft_id = request.GET.get("mid")
        account = MicrosoftConnectedAccounts.objects.filter(microsoft_id=microsoft_id)
        if len(account) == 0:
            return Response({"message": "User doesnot exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        account_info = {}
        account = account[0]
        
        token_data = get_tokens_for_user(account)
        access_token = token_data.get("access")
        refresh_token = token_data.get("refresh")
        
        account_info['access_token'] = access_token
        account_info['id'] = account.id
        account_info['microsoft_id'] = account.microsoft_id
        account_info['mail'] = account.mail_id
        account_info['given_name'] = account.given_name
        account_info['surname'] = account.surname
        account_info['user_principal_name'] = account.user_principal_name
        account_info['display_name'] = account.display_name
        account_info['refresh_token'] = refresh_token
        
        serializer = MicrosoftConnectAccountSerializer(account_info)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class GetUserMail(APIView):
    def get(self, request):
        try:
            jwt_auth_header = request.headers.get("Authorization")
            if jwt_auth_header and jwt_auth_header.startswith("Bearer "):
                jwt_access_token = jwt_auth_header.split(" ")[1]
            else:
                jwt_access_token = None
            if not jwt_access_token:
                return Response({"error": "Not Token"}, status=status.HTTP_401_UNAUTHORIZED)
            
            account = verify_access_token(jwt_access_token)
            if not account:
                return Response({"error": "User not found"}, status=status.HTTP_401_UNAUTHORIZED)
            
            filter = request.GET.get("filter")
            ms_access_token = account.access_token
            headers = {"Authorization": f"Bearer {ms_access_token}"}
            print(headers)
            
            def get_ms_messages(filter: str):
                return "https://graph.microsoft.com/v1.0/me/{}/messages".format(filter)
                
            def make_request(url, headers, account: MicrosoftConnectedAccounts):
                response = requests.get(url, headers=headers)
                if response.status_code == 401:
                    status_code, refresh_response = get_refresh_token(account.refresh_token)
                    
                    if status_code == 200:
                        refresh_data = refresh_response.json()
                        account.access_token = refresh_data.get("access_token")
                        account.refresh_token = refresh_data.get('refresh_token')
                        account.save()
                        
                        headers['Authorization'] = f"Bearer {account.access_token}"
                        return requests.get(url, headers=headers)
                    else:
                        return response
                return response
                
            match filter:
                case "sentitems":
                    url = get_ms_messages(filter)
                    response = make_request(url, headers, account)
                case "inbox":
                    url = get_ms_messages(filter)
                    response = make_request(url, headers, account)
                case "drafts":
                    url = get_ms_messages(filter)
                    response = make_request(url, headers, account)
                case _:
                    # Fetch top 10 messages
                    url = "https://graph.microsoft.com/v1.0/me/messages?$top=10"
                    response = make_request(url, headers, account)
            
            if response.status_code == 401:
                return Response({"error": "Microsoft authentication failure"}, status=status.HTTP_401_UNAUTHORIZED)
            
        except ExpiredTokenError as e:
            return Response({"error": "Token expired"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except InvalidToken as e:
            return Response({"error": "Invalid Token"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except TokenError as e:
            return Response({"error": "Token Error"}, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            return Response({"error": "Internal Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
        messages = response.json().get("value", [])
        return Response({'mails': messages}, status=status.HTTP_200_OK)