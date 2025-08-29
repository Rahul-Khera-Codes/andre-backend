from io import BytesIO
from traceback import format_exc
import uuid

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..client import clients
from ..utils.auth import verify_access_token
from ..utils.azure_ai import (
    create_vector_store_for_client,
    upload_files_to_vector_store,
    ask_question_with_vector_search
)
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
            
            document: InMemoryUploadedFile = serializer.validated_data.get("document")
            content_bytes = document.read()
            print("Type", type(content_bytes))
            file_data = {
                "name": document.name,
                "size": document.size,
                "type": document.content_type
            }
            
            question = "Summarize the document in 1 paragraph."
            
            def wrapped_files(files):
                wfiles = []
                for f in files:
                    if hasattr(f, "read"):  # InMemoryUploadedFile
                        content = f.read()
                        bio = BytesIO(content)
                        bio.name = f.name if f.name else "document.pdf"  # must have valid extension
                        f.seek(0)  # reset so Django can reuse if needed
                        wfiles.append(bio)
                    else:
                        wfiles.append(f)
                return wfiles
                        
            files = wrapped_files([document])
            
            account = request.user
            session_id = str(uuid.uuid4())
            vector_store = create_vector_store_for_client(clients.client_azure_openai, account)
            upload_files_to_vector_store(clients.client_azure_openai, vector_store.id, files)
            response = ask_question_with_vector_search(clients.client_azure_openai, MODEL, vector_store.id, session_id, question)
            
            print(f"Name: {file_data['name']}, size: {file_data['size']}, type: {file_data["type"]}")
            # print(dir(document))
            
            return Response({"message": response.output_text}, status=status.HTTP_201_CREATED  )
                
        except Exception as e:
            print(format_exc())
            return Response({"error": f"Internal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
        
# {
#     "id": "",
#     "file_name": "",
#     "file_size": "",
#     "summary": "",
#     "created": "",
#     "type": "pdf"
# }