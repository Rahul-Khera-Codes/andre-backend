import os
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import MicrosoftConnectedAccounts
from .utils import generate_access_token, get_user_info
from .tasks import new_user_mail_sync

class MicrosoftConnectVerify(APIView):
    def get(self, request):
        code = request.GET.get('code')
        print(code)
        
        status_code, response = generate_access_token(code)
        if status_code != 200:
            return redirect(f"{os.getenv("FRONTEND_URL")}/dashboard?response=error", status=status.HTTP_302_FOUND)
        
        access_token = response.get('access_token')
        refresh_token = response.get('refresh_token')
        
        status_code, user_data = get_user_info(access_token)
        
        if status_code !=200:
            return redirect(f"{os.getenv("FRONTEND_URL")}/dashboard?response=error", status=status.HTTP_302_FOUND)

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
                account = MicrosoftConnectedAccounts.objects.create(user_principal_name=user_principal_name,
                                                        microsoft_id=microsoft_id, display_name=display_name, surname=surname,
                                                        given_name=given_name, mail_id=mail,
                                                        access_token=access_token, refresh_token=refresh_token)
            new_user_mail_sync.delay(access_token, account.id)
        except Exception as e:
            print(e)
            return redirect(f"{os.getenv("FRONTEND_URL")}/dashboard?response=error", status=status.HTTP_302_FOUND)
        
        return redirect(f"{os.getenv("FRONTEND_URL")}/dashboard?response=success", status=status.HTTP_302_FOUND)
    
class GetConnectedAccounts(APIView):    
    def get(self, request):
        
        accounts = MicrosoftConnectedAccounts.objects.all()
        
        data = []
        
        for account in accounts:
            account_info = {}
            
            account_info['microsoft_id'] = account.id
            account_info['mail'] = account.mail_id
            account_info['given_name'] = account.given_name
            account_info['surname'] = account.surname
            account_info['user_principal_name'] = account.user_principal_name
            account_info['display_name'] = account.display_name
            
            data.append(account_info)
        
        return Response({'connected_accounts': data}, status=status.HTTP_200_OK)