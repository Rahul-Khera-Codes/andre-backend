import os
import uuid

from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv


load_dotenv()
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_ACCOUNT_CONNECTION_STRING")

dummy_storage = [
    {"firstname": "rahul", "lastname": "khera"},
    {"firstname": "lost", "lastname": "eagle"}
]

# 🔹 Generate valid container name
def generate_container_name(firstname: str, lastname: str) -> str:
    short_id = uuid.uuid4().hex[:8]  # short UUID for uniqueness
    container_name = f"{firstname}-{lastname}-{short_id}".lower()
    return container_name.replace(" ", "-")

# 🔹 Create container if it doesn’t exist
def create_client_container(connect_str: str, container_name: str):
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    container_client = blob_service_client.get_container_client(container_name)

    try:
        container_data = container_client.create_container()
        print(f"✅ Container created: {container_name}")
        print(container_data)
    except Exception as e:
        print(f"ℹ️ Container already exists or error: {e}")

    return container_client

# 🔹 Upload a document into the client’s container
def upload_document(container_client, file_path: str, blob_name: str = None):
    if blob_name is None:
        blob_name = file_path.split("/")[-1]  # use filename if not provided

    with open(file_path, "rb") as data:
        container_client.upload_blob(name=blob_name, data=data, overwrite=True)
        print(f"📂 Uploaded file '{blob_name}' to container '{container_client.container_name}'")

# ==============================
# Example usage
# ==============================
if __name__ == "__main__":
    # Your Azure Storage connection string
    connect_str = AZURE_STORAGE_CONNECTION_STRING

    for client in dummy_storage:

        # Generate container name
        container_name = generate_container_name(client.get("firstname"), client.get("lastname"))
        print(container_name)

        # Create/verify container
        container_client = create_client_container(connect_str, container_name)

        # Upload a document (change path to your file)
        file_path = "Visdomr - features MVP1.pdf"
        upload_document(container_client, file_path)
