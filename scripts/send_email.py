import os

from dotenv import load_dotenv
import requests

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0/me/sendMail"

def send_outlook_mail(access_token: str, subject: str, body: str, to_recipients: list):
    """
    Create a draft email in Outlook using Microsoft Graph API.
    
    :param access_token: OAuth2 access token for Microsoft Graph
    :param subject: Email subject
    :param body: Email body (HTML or text)
    :param to_recipients: List of recipient email addresses
    :return: Response JSON from Graph API
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Format recipients
    # recipients = [{"emailAddress": {"address": addr}} for addr in to_recipients]
    recipients = [
        {
            "emailAddress": {
                "address": "losteaglefound@gmail.com"
            }
        }
    ]

    FROM = 'rahul.excel2011@gmail.com'

    # Draft message payload
    payload = {
        "message": {
            "from": {
                "emailAddress": {
                    "address": FROM
                }
            },
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body
            },
            "toRecipients": recipients
        }    
    }
    

    response = requests.post(GRAPH_API_ENDPOINT, headers=headers, json=payload)

    if response.status_code in (200, 201, 202):
        return response.json()  # Draft created successfully
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")


# Example token and call (replace with a real token)
token = ACCESS_TOKEN

draft = send_outlook_mail(
    access_token=token,
    subject="Draft: Meeting Reminder",
    body="<p>Today date is 28 August 2025.</p>",
    to_recipients=["test@example.com"]
)

print("Draft created with ID:", draft["id"])
