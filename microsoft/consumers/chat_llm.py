from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from openai import APIError

from ..utils.azure_ai import TalkToYourDocument
from ..client import clients


class ChatLLMConsumer(AsyncJsonWebsocketConsumer):
    
    async def connect(self):
        await super().connect()
    
        self.account = self.scope.get('account')
        self.ttyd = TalkToYourDocument(account=self.account)
        await self.ttyd.create_vector_store_for_client(clients.client_azure_openai)
        await self.ttyd.get_or_create_session()
        
        print("vector_store:", await self.ttyd.vector_store_id)
        print("Session id:", await self.ttyd.session_id)
        # await ttyd.upload_files_to_vector_store(clients.client_azure_openai, files)

    
    async def receive_json(self, content, **kwargs):
        question = content.get("question", None);
        if not question:
            await self.send_json(content={
                "type": "error",
                "code": 1008,
                "reason": "Question is required"
            })
            
        response_output_text = ""
        response = await self.ttyd.ask_question_with_vector_search(
            clients.client_azure_openai, 
            settings.AZURE_MODEL_NAME,
            question,
            stream=True
        )
        
        async for i in response():
            response_output_text += i
            await self.send_json(content={"data_chunks": i})
        
        await self.ttyd.add_to_history("user", question)
        if response_output_text:
            await self.ttyd.add_to_history("assistant", response_output_text)