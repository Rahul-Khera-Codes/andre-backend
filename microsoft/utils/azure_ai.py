import uuid


from asgiref.sync import sync_to_async
from openai import AzureOpenAI
from openai.resources.vector_stores import VectorStores
from openai.types.vector_stores.vector_store_file_batch import VectorStoreFileBatch
from openai.types.vector_store import VectorStore

from ..utils.auth import get_vector_store_name
from ..client import clients
from ..models import (
    Message,
    MicrosoftConnectedAccounts,
    Session,
    VectorStore as VectorStoreModel,
)
from ..prompts import chat_llm_system_prompt

class TalkToYourDocument:
    def __init__(self, *, client: AzureOpenAI | None = None, account: MicrosoftConnectedAccounts | None = None) -> None:
        self.__client: AzureOpenAI = client if client else None
        self.__account =  account if account else None
        print("Account:", account, self.__account)
        self.__session_id: str | None = None
        self.__session_obj: Session | None = None
        self.__vector_store_id: str = None
        self.__vector_store: VectorStore | None = None
        self.__vector_store_obj: VectorStoreModel | None = None    
        self.system_prompt = chat_llm_system_prompt()
        
    async def get_or_create_session(self, session_id: str):
        self.__session_obj, session_created = await Session.objects.aget_or_create(
            vector_store=self.__vector_store_obj,
            microsoft=self.__account,
            session_id=session_id
        )
        if (
            session_created or 
            await sync_to_async(lambda: not self.__session_obj.session_id)()
        ):
            self.__session_id = self.__session_obj.session_id = str(uuid.uuid4())
            await self.__session_obj.asave()
        else:
            self.__session_id = self.__session_obj.session_id
        
    async def create_vector_store_for_client(
        self, 
        client: AzureOpenAI | None = None, 
        account: MicrosoftConnectedAccounts | None = None,
        vs_id: str | None = None
    ) -> VectorStore:
        """
        Create a vector stored and return `VectorStores` object.
        
        :param client: `AzureOpenAI` object.
        :param client_id: User id.
        :return: Return `VectorStores` object.
        """
        self.__vector_store_obj, vector_store_created = await VectorStoreModel.objects.aget_or_create(
            microsoft=self.__account
        )
        vector_store: VectorStore | None = None
        if (
            vector_store_created or 
            not self.__vector_store_obj.vector_store_id
        ):
            vector_store_name = await get_vector_store_name(self.__account)
            vector_store =  await sync_to_async(lambda: client.vector_stores.create(name=vector_store_name))()
            self.__vector_store_obj.vector_store_id = vector_store.id
            await self.__vector_store_obj.asave()
        else:
            vector_store = client.vector_stores.retrieve(self.__vector_store_obj.vector_store_id)
            
        self.__vector_store_id = self.__vector_store_obj.vector_store_id
        return vector_store
    
    @property
    async def vector_store_id(self):
        return self.__vector_store_id
    @vector_store_id.setter
    async def set_vector_store_id(self, store_id: str):
        self.__vector_store_id = store_id
    
    
    @property
    async def vector_store(self):
        return self.__vector_store
        
        
    @property
    async def session_id(self):
        return self.__session_id
    @session_id.setter
    async def set_session_id(self, sid: str):
        self.__session_id = sid
        
    @property
    async def session_obj(self):
        return self.__session_obj
    

    async def upload_files_to_vector_store(
        self, 
        client: AzureOpenAI,
        files: list[bytes]
    ) -> VectorStoreFileBatch:
        return client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=self.__vector_store_id,
            files=files
        )
        
        
    async def add_to_history(self, role: str, content: str):
        message_obj = await Message.objects.acreate(session=self.__session_obj, role=role, content=content)

        
    async def get_history(self):
        history = []
        messages_obj = await sync_to_async(lambda: Message.objects.filter(session=self.__session_obj))()
        await sync_to_async(lambda: history.extend([x.to_dict() for x in messages_obj]), thread_sensitive=False)()
        return history
            

    async def ask_question_with_vector_search(
        self, 
        client: AzureOpenAI, 
        model: str, 
        question: str,
        stream: bool = False
    ):
        # Build conversation history for context
        history = await self.get_history()
        # history = []
        
        # Add the new user question
        # history_plus_question = history + [{"role": "user", "content": question}]
        history_plus_question = history + [
            {"role": "system", "content": self.system_prompt}, 
            {"role": "user", "content": question}
        ]
        response = client.responses.create(
            model=model,
            input=history_plus_question,
            tools=[{
                "type": "file_search",
                "vector_store_ids": [self.__vector_store_id]
            }],
            stream=True,
        )
        
        async def stream_output():
            for event in response:
                if event.type == "response.output_text.delta":
                    yield event.delta
        
        if stream:
            return stream_output
        
        # Save user question and assistant response
        await self.add_to_history("user", question)
        if response.output_text:
            await self.add_to_history("assistant", response.output_text)
        return response.output_text
    