import asyncio

from adrf.views import APIView as AsynAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import MicrosoftConnectedAccounts
from ..utils.request_methods import get_onedrive_content
from ..exceptions import MSInvalidTokenError


class OneDriveView(AsynAPIView):
    permission_classes = [IsAuthenticated]
    
    async def get(self, request):
        try:
            print(request.query_params)
            folder_id=request.query_params.get("folder_id")
            print("Folder id:", folder_id)
            account: MicrosoftConnectedAccounts = request.user
            if folder_id:
                drive_response = await get_onedrive_content(account.access_token, account=account, folder_id=folder_id)
            else:
                drive_response = await get_onedrive_content(account.access_token, account=account)
            print("Drive response:", drive_response)
            return Response(drive_response, status=status.HTTP_200_OK)
        except MSInvalidTokenError as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)