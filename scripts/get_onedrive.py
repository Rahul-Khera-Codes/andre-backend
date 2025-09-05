import json
import os
import asyncio
import aiohttp
from typing import Any

from dotenv import load_dotenv

load_dotenv(override=True)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Graph API endpoint for listing root drive files

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

async def get_facet(f: dict[str, Any]):
    for facet in ['folder', 'file', 'image']:
        if facet in f.keys():
            return f[facet]

async def get_onedrive_content():
    url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                files = data.get("value", [])
                print("Files in OneDrive root:")
                for f in files:
                    print(json.dumps(f, indent=4))
                    # file_name = f['name']
                    # size = f['size']
                    # id = f['id']
                    # drive_type = f['parentReference']['driveType']
                    # drive_id = f['parentReference']['driveId']
                    # parent_path = f['parentReference']['path']
                    # facet_data = await get_facet(f)
            else:
                text = await response.text()
                print("Error:", response.status, text)
                
                
async def walk_onedrive():
    url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
    url_items = "https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}/children"

    async with aiohttp.ClientSession() as session:
        folder_ids_urls = [url]
        while len(folder_ids_urls) > 0:
            cur_url = folder_ids_urls.pop()
            print(cur_url)
            async with session.get(cur_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    values = data.get('value')
                    if not values:
                        continue
                    print("Values:", len(values))
                    for value in values:
                        if "folder" in value.keys():
                            print(value)
                            folder_id = value.get("id")
                            folder_ids_urls.insert(0, url_items.format(folder_id=folder_id))
                else:
                    print("Not authenticated")

if __name__ == "__main__":
    asyncio.run(walk_onedrive())
