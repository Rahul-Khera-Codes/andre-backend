import os, requests

from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

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

def get_mail_messages(access_token, time_filter):
    
    # url = f"https://graph.microsoft.com/v1.0/me/messages?$filter=receivedDateTime ge {time_filter}&$orderBy=receivedDateTime asc&$select=id,subject,from,receivedDateTime,bodyPreview,uniqueBody,body"
    # url = f"https://graph.microsoft.com/v1.0/me/messages?$orderBy=receivedDateTime asc&$select=id,subject,sender,toRecipients,from,createdDateTime,receivedDateTime,bodyPreview,uniqueBody,body"
    url = f"https://graph.microsoft.com/v1.0/me/messages?$orderBy=receivedDateTime desc&$select=id,subject,sender,toRecipients,from,createdDateTime,receivedDateTime,bodyPreview,uniqueBody,body"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    return response.status_code, response


def get_calendar_event(access_token, time_filter):
    
    # url = f"https://graph.microsoft.com/v1.0/me/messages?$filter=receivedDateTime ge {time_filter}&$orderBy=receivedDateTime asc&$select=id,subject,from,receivedDateTime,bodyPreview,uniqueBody,body"
    # url = f"https://graph.microsoft.com/v1.0/me/messages?$orderBy=receivedDateTime asc&$select=id,subject,sender,toRecipients,from,createdDateTime,receivedDateTime,bodyPreview,uniqueBody,body"
    url = f"https://graph.microsoft.com/v1.0/me/messages?$orderBy=receivedDateTime desc&$select=id,subject,sender,toRecipients,from,createdDateTime,receivedDateTime,bodyPreview,uniqueBody,body"
    
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
    
    response = requests.get(url, headers=headers, json=event_body)
    
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

def send_mail(access_token, subject, body, to_recipient):
    url = "https://graph.microsoft.com/v1.0/me/messages"
    
    headers = {"Authorization": f"Bearer {access_token}",
            "Accept": "application/json"}

    payload =  {
        "subject": subject,
        "importance":"Low",
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
        ],
    }

    response = requests.post(url, headers=headers, json=payload)
    
    return response.status_code, response.json()



def get_unique_body(message):
    body = message["content"]
    if message["contentType"] == "html":
        text = BeautifulSoup(body, "html.parser").get_text(separator="\n")
    else:
        text = body
    return text
