from typing import Literal

import requests


def create_draft_mail(access_token: str, sender: str, subject: str, body: str, body_content_type: Literal['html', 'text'] = "html", to_recipients: list[str] = []):
    """
    Create a draft email in Outlook using Microsoft Graph API.
    
    :param sender: Email address of sender
    :param access_token: OAuth2 access token for Microsoft Graph
    :param subject: Email subject
    :param body: Email body (HTML or text)
    :param to_recipients: List of recipient email addresses
    :return: Response Tuple of status_code, JSON Response from Graph API
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    recipients = [{"emailAddress": {"address": x}} for x in to_recipients]

    # Draft message payload
    message = {
        "from": {
            "emailAddress": {
                "address": sender
            }
        },
        "subject": subject,
        "body": {
            "contentType": body_content_type,
            "content": body
        },
        "toRecipients": recipients
    }

    response = requests.post(url="https://graph.microsoft.com/v1.0/me/messages", headers=headers, json=message)
    return response.status_code, response.json()


def send_outlook_mail(access_token: str, sender: str, subject: str, body: str, body_content_type: Literal['html', 'text'] = "html", to_recipients: list[str] = []):
    """
    Create a draft email in Outlook using Microsoft Graph API.
    
    :param sender: Sender email address
    :param access_token: OAuth2 access token for Microsoft Graph
    :param subject: Email subject
    :param body: Email body (HTML or text)
    :param to_recipients: List of recipient email addresses
    :return: Response Tuple of status_code, JSON Response from Graph API
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Format recipients
    recipients = [{"emailAddress": {"address": addr}} for addr in to_recipients]
    
    # Draft message payload
    payload = {
        "message": {
            "from": {
                "emailAddress": {
                    "address": sender
                }
            },
            "subject": subject,
            "body": {
                "contentType": body_content_type,
                "content": body
            },
            "toRecipients": recipients
        }    
    }
    
    response = requests.post(url="https://graph.microsoft.com/v1.0/me/sendMail", headers=headers, json=payload)
    return response.status_code, response.json()