
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..utils.auth import verify_access_token
from ..models import EmailMessages
from ..serializers import (
    DocumentSerializer,
    EmailMessageSerializer,
)


class SummarizeEmailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            message_id = request.data.get("message_id")
            email_message = EmailMessages(microsoft=request.user, message_id=message_id)
            serializer_email = EmailMessageSerializer(email_message)
            return Response(serializer_email.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Internal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
        
class DocumentSummarize(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            serializer = DocumentSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({"error": "Invalid file"}, status=status.HTTP_400_BAD_REQUEST)
            print(serializer.validated_data)
            document = serializer.validated_data.get("document")
            print(dir(document))
            return Response({"message": "Summarized successfully"}, status=status.HTTP_201_CREATED  )
                
        except Exception as e:
            return Response({"error": f"Internal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    