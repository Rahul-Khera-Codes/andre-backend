import os

from dotenv import load_dotenv
import requests

load_dotenv()


ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

def get_folder_map(access_token: str):
    """
    Fetch all Outlook mail folders and map folderId → displayName.

    :param access_token: OAuth2 access token for Microsoft Graph
    :return: dict mapping folderId to folder name
    """
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    GRAPH_API_FOLDERS_ENDPOINT = "https://graph.microsoft.com/v1.0/me/mailFolders"
    
    folder_map = {}
    url = GRAPH_API_FOLDERS_ENDPOINT

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Error {response.status_code}: {response.text}")

        data = response.json()
        print(data)

        for folder in data.get("value", []):
            folder_map[folder["id"]] = folder["displayName"]

        # handle paging if there are many folders
        url = data.get("@odata.nextLink")

    return folder_map


# Example usage
if __name__ == "__main__":
    token = ACCESS_TOKEN  # Replace with a real Graph access token
    folder_map = get_folder_map(token)

    print("Folder Mapping (id → name):")
    for fid, name in folder_map.items():
        print(f"{fid} → {name}")
