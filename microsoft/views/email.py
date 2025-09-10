from math import ceil
from traceback import format_exc

from adrf.views import APIView as AynsAPIView
from asgiref.sync import sync_to_async
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import (
    EmailMessages,
    MicrosoftConnectedAccounts
)
from ..serializers import (
    DraftSerializer,
    EmailMessageSerializer
)
from ..serializers.aserializers import (
    DraftSerializerAsync,
    EmailMessageSerializerAsync
)
from ..utils.mails import (
    create_draft_mail, 
    send_outlook_mail
)


def snake_to_camel(q: str):
    ql = q.split("_")
    nql = []
    for s in ql:
        nql.append(s[0].upper() + s[1:])
        
    return " ".join(nql)


class GetUserMail(AynsAPIView):
    permission_classes = [IsAuthenticated]
    
    async def get(self, request):
        try:
            mail_filter = request.query_params.get('filter')
            mail_filter = snake_to_camel(mail_filter)
            if mail_filter == "All" or mail_filter == 'all':
                mail_filter = None
            # Pagination params
            try:
                page = int(request.query_params.get("page", 1))
                page_size = int(request.query_params.get("page_size", 10))
            except ValueError:
                return Response({"error": "Invalid pagination parameter"}, status=status.HTTP_400_BAD_REQUEST)
            if page < 1 and page_size < 1:
                return Response({"error": "Page and page_size must be positive integers"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Filtering
            if mail_filter:
                emails_qs = await sync_to_async(
                    lambda: EmailMessages.objects.filter(Q(microsoft=request.user) & Q(folder_name=mail_filter)).order_by("-created")
                )()
            else: 
                emails_qs = await sync_to_async(
                    lambda: EmailMessages.objects.filter(microsoft=request.user).order_by("-created")
                )()
                
            # Get total count
            total_count = await sync_to_async(emails_qs.count)()
            total_pages = ceil(total_count / page_size) if page_size else 1
            # Pageinate
            start = (page - 1) * page_size
            end = start + page_size
            emails = await (sync_to_async(lambda: list(emails_qs[start:end])))()
            email_serializer = EmailMessageSerializerAsync(emails, many=True)
            data = await email_serializer.adata
            return Response({
                "pagination": {
                    "total_count": total_count,
                    "page": page,
                    "total_pages": total_pages
                },
                "emails": data
            }, status=status.HTTP_200_OK)    
        except Exception as e:
            print("error:", format_exc())
            return Response({"error": f"Internal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
    
    async def post(self, request):
        try:
            print("draft:", 1, request.data)
            serializer_mail = DraftSerializer(data=request.data)
            if not serializer_mail.is_valid():
                return Response({"error": serializer_mail.error_messages}, status=status.HTTP_400_BAD_REQUEST)
            print("draft:", 2)
            match serializer_mail.validated_data.get("filter"):
                case "draft":
                    print("draft:", 3)
                    account: MicrosoftConnectedAccounts = request.user
                    access_token = account.access_token
                    status_code, response = await sync_to_async(lambda: create_draft_mail(
                        access_token=access_token,
                        sender=account.mail_id,
                        body=serializer_mail.validated_data.get('body'),
                        body_content_type="html",
                        subject=serializer_mail.validated_data.get("subject"),
                        to_recipients=serializer_mail.validated_data.get("recipients")
                    ))()
                    if status_code not in (200, 201, 202):
                        print("Error response:", response)
                        return Response({"error": "error drafting mail"}, status=status.HTTP_400_BAD_REQUEST)
                case "send_mail":
                    print("draft:", 4)
                    recipients = serializer_mail.validated_data.get("recipients")
                    if len(recipients) == 0:
                        print(5)
                        return Response({"error": "recipients for sending mail can't be empty"}, status=status.HTTP_400_BAD_REQUEST) 
                    print(6)
                    account: MicrosoftConnectedAccounts = request.user
                    access_token = account.access_token
                    status_code, response = await sync_to_async(lambda: send_outlook_mail(
                        access_token=access_token,
                        sender=account.mail_id,
                        body=serializer_mail.validated_data.get('body'),
                        body_content_type="html",
                        subject=serializer_mail.validated_data.get("subject"),
                        to_recipients=serializer_mail.validated_data.get("recipients")
                    ))()
                    if status_code not in (200, 201, 202):
                        print("Error response:", response)
                        return Response({"error": "error drafting mail"}, status=status.HTTP_400_BAD_REQUEST)
                case _:
                    return Response({"error": "Invalid mail request"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "draft mail saved successfully"}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            print(format_exc())
            return Response({"error": f"Interal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class GetMailFolder(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):    
        try:
            emails = EmailMessages.objects.filter(microsoft=request.user)
            folder_name = emails.values_list("folder_name", flat=True).distinct()
            
        except Exception as e:
            print("error:", e)
            return Response({"error": f"Internal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
        # messages = response.json().get("value", [])
        # print("messages:", messages)
        return Response(folder_name, status=status.HTTP_200_OK)
    
    