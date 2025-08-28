from traceback import format_exc

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


class GetUserMail(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            mail_filter = request.query_params.get('filter')
            mail_filter = snake_to_camel(mail_filter)
            if mail_filter == "All" or mail_filter == 'all':
                mail_filter = None
            
            if mail_filter:
                emails = EmailMessages.objects.filter(Q(microsoft=request.user) & Q(folder_name=mail_filter))
            else:
                emails = EmailMessages.objects.filter(microsoft=request.user)
            email_serializer = EmailMessageSerializer(emails, many=True)
            return Response(email_serializer.data, status=status.HTTP_200_OK)    
        except Exception as e:
            print("error:", e)
            return Response({"error": f"Internal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
    
    def post(self, request):
        try:
            print("draft:", 1)
            serializer_mail = DraftSerializer(data=request.data)
            if not serializer_mail.is_valid():
                return Response({"error": serializer_mail.error_messages}, status=status.HTTP_400_BAD_REQUEST)
            print("draft:", 2)
            match serializer_mail.validated_data.get("filter"):
                case "draft":
                    print("draft:", 3)
                    account: MicrosoftConnectedAccounts = request.user
                    access_token = account.access_token
                    status_code, response = create_draft_mail(
                        access_token=access_token,
                        sender=account.mail_id,
                        body=serializer_mail.validated_data.get('body'),
                        body_content_type="html",
                        subject=serializer_mail.validated_data.get("subject"),
                        to_recipients=serializer_mail.validated_data.get("recipients")
                    )
                    if status_code not in (200, 201, 202):
                        print("Error response:", response)
                        return Response({"error": "error drafting mail"}, status=status.HTTP_400_BAD_REQUEST)
                case "send_mail":
                    ...
            return Response({"message": "draft saved successfully"}, status=status.HTTP_201_CREATED)
        
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
    
    