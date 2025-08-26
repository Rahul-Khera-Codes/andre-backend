import base64
import os

from dotenv import load_dotenv
import requests

# assert not load_dotenv()
print(load_dotenv())

access_token = os.getenv("ACCESS_TOKEN")

# print(access_token, os.getenv("REDIRECT_URI"))

headers = {
    "Authorization": f"Bearer {access_token}"
}

# Fetch top 10 messages
url = "https://graph.microsoft.com/v1.0/me/messages?$top=99&$orderBy=receivedDateTime asc"
# url = "https://graph.microsoft.com/v1.0/me/sentitems/messages"
url_attachment_lists = 'https://graph.microsoft.com/v1.0/me/messages/{}/attachments'

response = requests.get(url, headers=headers)

if response.status_code == 200:
    messages = response.json().get("value", [])
    for msg in messages:
        print(msg)
        print("Subject:", msg.get("subject"))
        print("From:", msg.get("from", {}).get("emailAddress", {}).get("address"))
        print("Received:", msg.get("receivedDateTime"))
        # print("Preview:", msg.get("bodyPreview"))
        print("toRecipients:", msg.get('toRecipients'))
        print("isDraft:", msg.get("isDraft"))
        
        if msg.get("hasAttachments"):
            message_id = msg.get('id')
            response_attachments_list = requests.get(url_attachment_lists.format(message_id), headers=headers)
            if response_attachments_list.status_code == 200:
                attachments = response_attachments_list.json()
                for file in attachments.get("value"):
                    name, content_bytes = file.get("name"), file.get("contentBytes")
                    with open(name, 'wb') as f:
                        content = base64.b64decode(content_bytes)
                        f.write(content)
            
        print("-" * 50)
else:
    print("Error:", response.status_code, response.text)
