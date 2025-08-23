import base64
from datetime import datetime, timezone, timedelta
from operator import itemgetter
import os
import re

from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests

# assert not load_dotenv()
print(load_dotenv())

access_token = os.getenv("ACCESS_TOKEN")

headers = {
    "Authorization": f"Bearer {access_token}"
}

# Fetch top 10 messages
# url = "https://graph.microsoft.com/v1.0/me/messages?$top=10&$filter=receivedDateTime ge {}&orderBy=receivedDateTime asc"
# url = "https://graph.microsoft.com/v1.0/me/messages?$top=10&$orderby=receivedDateTime desc&$select=id,subject,from,receivedDateTime,bodyPreview"
# url = "https://graph.microsoft.com/v1.0/me/messages?$orderBy=receivedDateTime desc&$select=id,subject,sender,toRecipients,from,createdDateTime,receivedDateTime,bodyPreview,uniqueBody,body"
# url = "https://graph.microsoft.com/v1.0/me/messages?$select=id,subject,sender,toRecipients,from,createdDateTime,receivedDateTime,bodyPreview,uniqueBody,body"
url = "https://graph.microsoft.com/v1.0/me/messages?$$filter=receivedDateTime ge {}&select=id,subject,sender,toRecipients,from,createdDateTime,receivedDateTime,bodyPreview,uniqueBody,body"
url_latest_mail = "https://graph.microsoft.com/v1.0/me/messages?$filter=conversationId eq '{}'"
url_message_body = "https://graph.microsoft.com/v1.0/me/messages/{}?$select=body"
# url_latest_mail = "https://graph.microsoft.com/v1.0/me/conversations/{}/threads"

# url = "https://graph.microsoft.com/v1.0/me/sentitems/messages"
url_attachment_lists = 'https://graph.microsoft.com/v1.0/me/messages/{}/attachments'


minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
time_filter = minutes_ago.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
url_formatted = url.format(time_filter)
# print("22222222222222222222222222222", url_formatted)
response = requests.get(url_formatted, headers=headers)

conversations_id_scraped = []

def get_body(message):

    # 1. Parse HTML
    soup = BeautifulSoup(message, "html.parser")
    text = soup.get_text()

    # 2. Common reply markers to split on
    # patterns = [
    #     r"On .* wrote:",             # Gmail/Outlook reply
    #     r"From:.*\n",                # Outlook headers
    #     r"Sent:.*\n",
    #     r"To:.*\n",
    #     r"Subject:.*\n",
    #     r"^-{2,}.*Original Message.*", # -----Original Message-----
    # ]

    # for pattern in patterns:
    #     match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    #     if match:
    #         text = text[:match.start()].strip()
    #         break

    # return text.strip()
    return text.split("From:")[0]


def get_unique_body(message):
    body = message["uniqueBody"]["content"]
    if message["uniqueBody"]["contentType"] == "html":
        text = BeautifulSoup(body, "html.parser").get_text(separator="\n")
    else:
        text = body
    return text

if response.status_code == 200:
    messages = response.json().get("value", [])[::-1]
    
    print("Total messages:", len(messages))
    # print(messages)
    
    for msg in messages:
        # print(msg)
        next_page = msg.get("@odata.nextLink")
        print("Next page:", next_page)
        print("Subject:", msg.get("subject"))
        print("From:", msg.get("from", {}).get("emailAddress", {}).get("address"))
        print("Recipients:", msg.get("toRecipients"))
        print("Received:", msg.get("receivedDateTime"))
        # print("Preview:", msg.get("bodyPreview"))
        # print("Body:", get_body(msg.get('body').get('content')))
        print("Unique body:", get_unique_body(msg))
        
        conversation_id = msg.get("conversationId")
        print("id:", msg.get('id'))
        print("conversation_id:", conversation_id)
        
        # response_msg_body = requests.get(url_message_body.format(msg.get('id')), headers=headers)
        # print(response_msg_body.status_code, response_msg_body.json())
        # if response_msg_body == 200:
        #     print("body:", response_msg_body.json())
        
        # response = requests.get(url_latest_mail.format(conversation_id), headers=headers)
        # if response.status_code == 200:
        #     print("Latest message:", response)
        #     conversations_id_scraped.append(conversation_id)
        
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
