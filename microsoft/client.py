import os

from django.conf import settings
from azure.storage.blob import BlobServiceClient
from openai import AzureOpenAI


class Client:
    client_azure_openai: AzureOpenAI | None
    blob_service_client: BlobServiceClient | None
    
    @classmethod
    def initialize_azure_openai(cls):
        cls.client_azure_openai = AzureOpenAI(
            api_version=settings.AZURE_API_VERSION,
            azure_endpoint=settings.AZURE_ENDPOINT,
            api_key=settings.AZURE_API_KEY
        )
        
    @classmethod
    def initialize_blob_client(cls):
        cls.blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_ACCOUNT_CONNECTION_STRING)
        
    @classmethod
    def initialize_clients(cls):
        cls.initialize_azure_openai()
        cls.initialize_blob_client()

def initialize_clients():
    Client.initialize_clients()
    
initialize_clients()
clients = Client