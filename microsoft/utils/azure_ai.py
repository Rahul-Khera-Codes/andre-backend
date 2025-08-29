from openai import AzureOpenAI
from openai.resources.vector_stores import VectorStores
from openai.types.vector_stores.vector_store_file_batch import VectorStoreFileBatch

from ..client import clients
from ..models import (
    Message,
    MicrosoftConnectedAccounts,
    Session,
    VectorStore,
    
)


def create_vector_store_for_client(client: AzureOpenAI, account: MicrosoftConnectedAccounts) -> VectorStores:
    """
    Create a vector stored and return `VectorStores` object.
    
    :param client: `AzureOpenAI` object.
    :param client_id: User id.
    :return: Return `VectorStores` object.
    """
    vector_store =  client.vector_stores.create(name=f"ai_{account.id}")
    vector_store_obj = VectorStore.objects.create(vector_store_id=vector_store.id, microsoft=account)
    return vector_store


def upload_files_to_vector_store(
    client: AzureOpenAI, 
    vector_store_id: str, 
    file_bytes: list[bytes]
) -> VectorStoreFileBatch:
    return client.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store_id,
        files=file_bytes
    )
    

def add_to_history(session_id: str, role: str, content: str):
    session_obj, session_created = Session.objects.get_or_create(session_id=session_id)
    message_obj = Message.objects.create(session=session_obj, role=role, content=content)
    
    
def get_history(session_id: str):
    session_obj, session_created = Session.objects.get_or_create(session_id=session_id)
    history = []
    if not session_created:
        messages_obj = Message.objects.filter(session=session_obj)
        history.extend([x.to_dict() for x in messages_obj])
    return history
        

def ask_question_with_vector_search(client, model: str, vector_store_id: str, session_id: str, question: str):
    # Build conversation history for context
    history = get_history(session_id=session_id)
        
        
    # Add the new user question
    history_plus_question = history + [{"role": "user", "content": question}]
    response = client.responses.create(
        model=model,
        input=history_plus_question,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vector_store_id]
        }],
        stream=False,
    )
    # Save user question and assistant response
    add_to_history(session_id, "user", question)
    if response.choices and response.choices[0].message and hasattr(response.choices[0].message, "content"):
        add_to_history(session_id, "assistant", response.choices[0].message.content)
    return response