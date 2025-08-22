import os

from django.conf import settings
from openai import AzureOpenAI


client_azure_openai = AzureOpenAI(
    api_version=settings.AZURE_API_VERSION,
    azure_endpoint=settings.AZURE_ENDPOINT,
    api_key=settings.AZURE_API_KEY
)