import asyncio
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from traceback import format_exc
import uuid

from adrf.views import APIView as AyncAPIView
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.exceptions import (
    MultipleObjectsReturned,
    ObjectDoesNotExist
)
from django.db.models import Q
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..client import clients
from ..utils.auth import verify_access_token
from ..utils.azure_ai import TalkToYourDocument
from ..utils.response import async_to_sync_stream_response_consumer
from ..models import (
    EmailMessages,
    Message,
    Session,
    VectorStore
)
from ..serializers import (
    DocumentSerializer,
    EmailMessageSerializer,
)
from ..serializers.aserializers import (
    DocumentSerializerAsync,
    EmailMessageSerializerAsync,
)
from ..serializers.achatbot import MessageSerializerAsync, SessionSerializerAsync


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
    


class DocumentSummarize(AyncAPIView):
    permission_classes = [IsAuthenticated]
    
    async def post(self, request):
        try:
            serializer = DocumentSerializerAsync(data=request.data)
            if not serializer.is_valid():
                return Response({"error": "Invalid file"}, status=status.HTTP_400_BAD_REQUEST)
            
            document: InMemoryUploadedFile = serializer.validated_data.get("document")
            # content_bytes = document.read()
            # print("Type", type(content_bytes))
            file_data = {
                "name": document.name,
                "size": document.size,
                "type": document.content_type
            }
            
            question = "Could you tell me about the content for file: {}".format(document.name)
            print("Question:", question)
            
            def wrapped_files(files):
                wfiles = []
                for f in files:
                    # InMemoryUploadedFile
                    content = f.read()
                    bio = BytesIO(content)
                    bio.name = f.name if f.name else "document.pdf"  # must have valid extension
                    f.seek(0)  # reset so Django can reuse if needed
                    wfiles.append(bio)
                return wfiles
                        
            files = wrapped_files([document])
            print("Files length:", len(files))
            
            account = request.user
            ttyd = TalkToYourDocument(account=account)
            await ttyd.create_vector_store_for_client(clients.client_azure_openai)
            # await ttyd.get_or_create_session()
            
            print("vector_store:", await ttyd.vector_store_id)
            print("Session id:", await ttyd.session_id)
            await ttyd.upload_files_to_vector_store(clients.client_azure_openai, files)

            # stream = True
            # response = await ttyd.ask_question_with_vector_search(
            #     clients.client_azure_openai, 
            #     settings.AZURE_MODEL_NAME,
            #     question,
            #     stream=stream
            # )
            
            # print(f"Name: {file_data['name']}, size: {file_data['size']}, type: {file_data["type"]}")
            # if stream:    
            #     # output = ""
            #     # async for x in response():
            #     #     print(x)
            #     #     output+=x
                
            #     return StreamingHttpResponse(
            #         async_to_sync_stream_response_consumer(response()), 
            #         content_type="text/plain"
            #     )
            
            # file_data.update({"summary": response.output_text})
            # return Response({"message": file_data}, status=status.HTTP_201_CREATED  )
            return Response({"message": "File uploaded successfully"}, status=status.HTTP_202_ACCEPTED)
            
        
        except ObjectDoesNotExist as e:
            model_class = e.__class__.model
            print("Model:", model_class.__name__)
        
        except MultipleObjectsReturned as e:
            model_class = e.__class__.model
            print("Model:", model_class.__name__)
            return Response({"error": f"Internal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        
        
        except Exception as e:
            print(format_exc())
            return Response({"error": f"Internal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
        
        
class ChatBotHistory(AyncAPIView):
    permission_classes = [IsAuthenticated]
    async def get(self, request):
        try:
            conversation_id = request.query_params.get("conversation_id")
            if conversation_id:
                sessions = await sync_to_async(
                    lambda: Session.objects.filter(Q(microsoft=request.user) & Q(session_id=conversation_id) & Q(deleted=False)).first()
                )()
                if not sessions:
                    return Response({"error": "Conversation not found"}, status=status.HTTP_400_BAD_REQUEST)
                messages = Message.objects.filter(Q(session=sessions.id)).all()
                await sync_to_async(
                    lambda: print(("Messages:", messages))
                )()
                messages_serializer = MessageSerializerAsync(messages, many=True)
                return Response({"messages": await messages_serializer.adata}, status=status.HTTP_200_OK)
                
            sessions = Session.objects.filter(Q(microsoft=request.user) & Q(deleted=False)).all()
            session_serializer = SessionSerializerAsync(sessions, many=True)
            return Response({"session": await session_serializer.adata}, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    def delete_all_converstaions(self, sessions):
        for s in sessions:
            s.deleted = True
            s.save()
            
    async def execute_delete_all_conversations(self, sessions):
        loop = asyncio.get_running_loop()
        loop.run_in_executor(
            ThreadPoolExecutor(),
            self.delete_all_converstaions,
            sessions
        )
            
    async def delete(self, request):
        try:
            conversation_id = request.query_params.get("conversation_id")
            if conversation_id:
                session = await sync_to_async(
                    lambda: Session.objects.filter(Q(microsoft=request.user) & Q(session_id=conversation_id)).first()
                )()
                session.deleted = True
                await session.asave()
                return Response({"message": "Conversation deleted successfully"}, status=status.HTTP_200_OK)
                
            sessions = Session.objects.filter(Q(microsoft=request.user) & Q(deleted=False)).all()
            await self.execute_delete_all_conversations(sessions)
                
            return Response({"messages": "All conversation deleted successfully"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(format_exc())
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
# {
#     "id": "",
#     "file_name": "",
#     "file_size": "",
#     "summary": "",
#     "created": "",``
#     "type": "pdf"
# }