import os
import requests

from dotenv import load_dotenv

load_dotenv(override=True)

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# Graph API endpoint for listing root drive files
url = "https://graph.microsoft.com/v1.0/sites?search=*"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    files = response.json().get("value", [])
    print("Files in OneDrive root:")
    for f in files:
        print(f"- {f['name']} (id: {f['id']})")
else:
    print("Error:", response.status_code, response.text)
