import os, requests

from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from ..exceptions import MSInvalidTokenError

def generate_access_token(code):
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        
    data = {"client_id": os.getenv("CLIENT_ID"),
            "client_secret": os.getenv("CLIENT_SECRET"),
            "code": code,
            "redirect_uri": os.getenv("REDIRECT_URI"),
            "grant_type": "authorization_code"}
    
    response = requests.post(url, data=data)
    
    return response.status_code, response.json()

def get_user_info(access_token):
    
    url = "https://graph.microsoft.com/v1.0/me"
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    return response.status_code, response.json()


def get_mail_messages(access_token, time_filter: str | None = None, new_user: bool = False):
    
    # if new_user is True, fetch latest 50 emails.
    # else user time_filter for background sync jjobs
    if new_user:
        url = f"https://graph.microsoft.com/v1.0/me/messages?$top=50&$orderBy=receivedDateTime asc&$select=id,subject,from,sender,receivedDateTime,bodyPreview,uniqueBody,body,toRecipients,isDraft,parentFolderId,hasAttachments,sentDateTime,receivedDateTime,createdDateTime,conversationId"
    else:
        url = f"https://graph.microsoft.com/v1.0/me/messages?$filter=receivedDateTime ge {time_filter}&$orderBy=receivedDateTime asc&$select=id,subject,sender,from,receivedDateTime,bodyPreview,uniqueBody,body,toRecipients,isDraft,parentFolderId,hasAttachments,sentDateTime,receivedDateTime,createdDateTime,conversationId"
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    return response.status_code, response



def get_mail_messages_loop_all(access_token, time_filter, url: str | None = None):
    
    if not url:
        # url = f"https://graph.microsoft.com/v1.0/me/messages?$filter=receivedDateTime ge {time_filter}&$orderBy=receivedDateTime asc&$select=id,subject,from,receivedDateTime,bodyPreview,uniqueBody,body"
        # url = f"https://graph.microsoft.com/v1.0/me/messages?$orderBy=receivedDateTime asc&$select=id,subject,sender,toRecipients,from,createdDateTime,receivedDateTime,bodyPreview,uniqueBody,body"
        url = f"https://graph.microsoft.com/v1.0/me/messages?$orderBy=receivedDateTime desc&$select=id,subject,sender,toRecipients,from,createdDateTime,receivedDateTime,bodyPreview,uniqueBody,body"
        # url = f"https://graph.microsoft.com/v1.0/me/messages"
        
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    return response.status_code, response


def get_calendar_event(access_token, time_filter):
    
    # url = f"https://graph.microsoft.com/v1.0/me/messages?$filter=receivedDateTime ge {time_filter}&$orderBy=receivedDateTime asc&$select=id,subject,from,receivedDateTime,bodyPreview,uniqueBody,body"
    # url = f"https://graph.microsoft.com/v1.0/me/messages?$orderBy=receivedDateTime asc&$select=id,subject,sender,toRecipients,from,createdDateTime,receivedDateTime,bodyPreview,uniqueBody,body"
    url = "https://graph.microsoft.com/v1.0/me/events?$select=subject,start,end,reminderMinutesBeforeStart"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    return response.status_code, response


def create_calendar_event(access_token: str, event_body: dict, /):
    url = f"https://graph.microsoft.com/v1.0/me/events"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=event_body)
    
    return response.status_code, response.json()


def get_refresh_token(refresh_token):
    
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    
    data = {
        'client_id': os.getenv("CLIENT_ID"),
        'scope': os.getenv("SCOPE"),
        'refresh_token': refresh_token,
        'grant_type': "refresh_token",
        'client_secret': os.getenv("CLIENT_SECRET")
    }
    
    response = requests.post(url, data=data)
    
    return response.status_code, response


def send_mail(access_token: str, subject: str, body: str, to_recipient: str):
    url = "https://graph.microsoft.com/v1.0/me/sendMail"
    
    headers = {"Authorization": f"Bearer {access_token}",
            "Accept": "application/json"}

    email_msg = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to_recipient
                    }
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=email_msg)
    
    return response.status_code, response.content.decode("utf-8")



def get_unique_body(message):
    body = message["content"]
    if message["contentType"] == "html":
        text = BeautifulSoup(body, "html.parser").get_text(separator="\n")
    else:
        text = body
    return text


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
            raise MSInvalidTokenError(f"Error {response.status_code}: {response.text}")
                
        data = response.json()

        for folder in data.get("value", []):
            folder_map[folder["id"]] = folder["displayName"]

        # handle paging if there are many folders
        url = data.get("@odata.nextLink")

    return folder_map

def get_attachments(access_token: str, message_id: str) -> tuple[int, list[dict]]:
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    url_attachment_lists = 'https://graph.microsoft.com/v1.0/me/messages/{}/attachments'
    response = requests.get(url_attachment_lists.format(message_id), headers=headers)
    return response.status_code, response.json()