import uuid

from azure.storage.blob import (
    BlobServiceClient, 
    ContainerClient
)

def generate_container_name(firstname: str, lastname: str) -> str:
    short_id = uuid.uuid4().hex[:8]  # short UUID for uniqueness
    container_name = f"{firstname}-{lastname}-{short_id}".lower()
    return container_name.replace(" ", "-")

def create_container(
    container_client: ContainerClient
) -> bool:
    try:
        container_client.create_container()
        print("Container created successfully")
        return True
    except Exception as e:
        print("Error creating container")
        return False
    
def get_container_client(client: BlobServiceClient, container_name: str) -> ContainerClient:
    return client.get_container_client(container_name)
    
def upload_files_to_container(
    container_client: ContainerClient,
    file_id: str,
    file_bytes: bytes,
    file_name: str
):
    container_client.upload_blob(
        name=file_id, 
        data=file_bytes, 
        metadata={"name": file_name}
    )