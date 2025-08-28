import os
from traceback import format_exc

from django.shortcuts import redirect
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import (
    RefreshToken
)

from ..client import clients
from ..models import (
    MicrosoftConnectedAccounts,
    UserToken
)
from ..utils import generate_access_token, get_refresh_token, get_user_info
from ..utils.auth import (
    get_callback_session_id,
    get_tokens_for_user,
)
from ..utils.storage import (
    create_container,
    get_container_client,
    generate_container_name
)
from ..tasks import new_user_mail_sync
from ..serializers import (
    MicrosoftConnectAccountSerializer,
    RefreshTokenSerailizer
)


class MicrosoftConnectVerify(APIView):
    def get(self, request):
        code = request.GET.get('code')
        # print(code)
        
        status_code, response = generate_access_token(code)
        # print("1", status_code)
        if status_code != 200:
            return redirect(f"{os.getenv("FRONTEND_URL")}?response=error", status=status.HTTP_302_FOUND)
        
        access_token = response.get('access_token')
        refresh_token = response.get('refresh_token')
        # print("Access_token:", access_token)
        
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
                print("Container name:", account.container_name)
                if not account.container_name:
                    container_name = generate_container_name(account.given_name, account.surname)
                    container_client = get_container_client(clients.blob_service_client, container_name)
                    create_container(container_client)
                    account.container_name = container_name
                
                account.access_token = access_token
                account.refresh_token = refresh_token
                account.save()
            
                
            if not account:
                container_name = generate_container_name(given_name, surname)
                container_client = get_container_client(clients.blob_service_client, container_name)
                create_container(container_client)
                
                account = MicrosoftConnectedAccounts.objects.create(
                    access_token=access_token,
                    container_name=container_name, 
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
            session_id = get_callback_session_id(mid = account.microsoft_id)
            
        except Exception as e:
            print(e)
            return redirect(f"{os.getenv("FRONTEND_URL")}/dashboard?response=error", status=status.HTTP_302_FOUND)
        
        return redirect(f"{os.getenv("FRONTEND_URL")}/dashboard?response=success&mid={microsoft_id}&sid={session_id}", status=status.HTTP_302_FOUND)
    
    
class GetConnectedAccounts(APIView):    
    def get(self, request):
        microsoft_id = request.GET.get("mid")
        session_id = request.GET.get("sid")
        print("MID:", microsoft_id, "SID:", session_id)
        account = MicrosoftConnectedAccounts.objects.filter(microsoft_id=microsoft_id).first()
        if not account:
            return Response({"message": "User doesnot exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        token_data = get_tokens_for_user(account)
        access_token = token_data.get("access")
        refresh_token = token_data.get("refresh")
        
        user_token_obj: UserToken | None = None
        try:
            user_token_obj = UserToken.objects.get(microsoft=account)
            user_token_obj.refresh_token = refresh_token
            user_token_obj.access_token = access_token
            user_token_obj.save()
        except UserToken.DoesNotExist:
            user_token_obj = UserToken.objects.create(
                access_token=access_token, 
                refresh_token=refresh_token, 
                microsoft=account
            )
        except Exception as e:
            return Response({"error": f"Error in creating user token: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if not user_token_obj:
            return Response({"error": f"Error in creating user token: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = MicrosoftConnectAccountSerializer(account)        
        response = serializer.data
        response.update({
            "access_token": user_token_obj.access_token,
            "refresh_token": user_token_obj.refresh_token
        })
        
        return Response(response, status=status.HTTP_200_OK)
    

class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.data.get("token")
        print("Refresh token:", refresh_token)
        if not refresh_token:
            return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_token_obj = UserToken.objects.filter(refresh_token=refresh_token).first()
            if not user_token_obj:
                return Response({"error": "Invalid refresh token, please login again"}, status=status.HTTP_401_UNAUTHORIZED)
            
            refresh = RefreshToken(refresh_token)
            new_access_token = refresh.access_token
            
            user_token_obj.access_token = new_access_token
            user_token_obj.save()
            
            data = {'token': new_access_token}
            serializers = RefreshTokenSerailizer(data)
            
            return Response(serializers.data, status=status.HTTP_201_CREATED)            

        except Exception as e:
            print(format_exc())
            return Response({"error": f"Internal error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

