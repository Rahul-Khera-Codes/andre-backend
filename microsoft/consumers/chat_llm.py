import json
from typing import Literal

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from openai import APIError

from ..utils.azure_ai import TalkToYourDocument
from ..client import clients
from ..models import Session


class ChatLLMConsumer(AsyncJsonWebsocketConsumer):
    
    async def connect(self):
        await super().connect()
    
        self.account = self.scope.get('account')
        if not self.account:
            await self.close(code=4003)
            return
        
        self.ttyd = TalkToYourDocument(account=self.account)
        await self.ttyd.create_vector_store_for_client(clients.client_azure_openai)
        print("vector_store:", await self.ttyd.vector_store_id)
        # await ttyd.upload_files_to_vector_store(clients.client_azure_openai, files)

    
    async def receive_json(self, content, **kwargs):
        
        question = content.get("question", None)
        conversation_id = content.get("conversation_id", None)
        conversation_type: Literal['new', 'existing'] = content.get('conversation_type', None)
        
        if conversation_id:
            match conversation_type:
                case "existing":
                    print("Searching for existing conversation.")
                    await self.ttyd.get_or_create_session(conversation_id)            
                    print("Session id:", await self.ttyd.session_id)
                case "new":
                    print("Creating new conversation.")
                    await self.ttyd.get_or_create_session(conversation_id)            
                    print("Session id:", await self.ttyd.session_id)
                    
                    if question and self.ttyd:
                        session_obj: Session = await self.ttyd.session_obj
                        session_obj.session_name = question[:20]
                        await session_obj.asave()
        
        if not self.ttyd.session_id:
            await self.send_json(content={
                "type": "error",
                "code": 1008,
                "reason": "Internal error: Error creating or searching conversation"
            })
            return
        
        print("Question:", question)
        if not question:
            await self.send_json(content={
                "type": "error",
                "code": 1008,
                "reason": "Question is required"
            })
            return
        
            
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
            
    async def receive(self, text_data=None, bytes_data=None, close=False):
        try:
            # print("Recived data:", text_data, bytes_data)
            return await super().receive(text_data, bytes_data, close=close)
        except json.JSONDecodeError as e:
            return await self.send_json({
                "type": "error",
                "code": 1008,
                "reason": "Incorrect payload, JSON required", 
            })