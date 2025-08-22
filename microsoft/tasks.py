import json, time
from celery import shared_task
from datetime import date, datetime, timedelta, timezone

from .graph import summarize_email_content
from .models import (
    EmailMessages, 
    MicrosoftConnectedAccounts, 
    Summarization
)
from .utils import (
    create_calendar_event,
    get_mail_messages,
    get_refresh_token
)


@shared_task
def mail_retrieve():
    
    accounts = MicrosoftConnectedAccounts.objects.all()
    if accounts:
        for account in accounts:
            access_token = account.access_token
            refresh_token = account.refresh_token
            minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
            time_filter = minutes_ago.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
            status_code, response = get_mail_messages(access_token, time_filter)
            
            if status_code != 200:
                status_code, response = get_refresh_token(refresh_token)
                
                if status_code != 200:
                    continue
                
                response = response.json()
                access_token = response.get('access_token')
                refresh_token = response.get('refresh_token')
                account.access_token  = access_token
                account.refresh_token = refresh_token
                account.save()
                
                status_code, response = get_mail_messages(access_token, time_filter)
                
                if status_code != 200:
                    continue
                
            response = response.json()

            values = response.get('value')
            if values:
                for value in values:
                    email_payload = {}
                    message_id = value.get('id')
    
                    message = EmailMessages.objects.filter(message_id=message_id, microsoft=account).first()
                    if message:
                        continue
                    
                    conversation_id = value.get('conversationId')
                    email_payload['conversation_id'] = conversation_id
                    # conversation = EmailMessages.objects.filter(conversation_id=conversation_id, microsoft=account).first()
                    
                    email_payload['message_id'] = value.get('id')
                    email_payload['subject'] = value.get('subject')
                    email_payload['body_preview'] = value.get('bodyPreview')
                    email_payload['content'] = value['body']['content']
                    sender = ""
                    sender = value.get('sender')
                    if sender:
                        email_payload['sender_email'] = sender['emailAddress']['address']
                    to_recipients = value.get('toRecipients')
                    to_recipient_emails = []
                    if to_recipients:
                        for to_recipient in to_recipients:
                            to_recipient_email = to_recipient['emailAddress']['address']
                            to_recipient_emails.append(to_recipient_email)
                    email_payload['to_recipient_emails'] = to_recipient_emails
                    email_payload['mail_time'] = value.get('createdDateTime')
    
                    email: EmailMessages = EmailMessages.objects.create(**email_payload, microsoft=account)
                    
                    summarized_content = summarize_email_content(email_content=email.content, subject=email.subject)
                    summarized_email_content = summarized_content.get("summary")
                    summarized_calendar_task = summarized_content.get("calendar", None)
                    if not summarized_calendar_task:
                        summarization = Summarization.objects.create(email=email, microsoft=account, summary=summarized_email_content)
                        print("summarization created successfully with not calendar event")
                    else:
                        summarization = Summarization.objects.create(email=email, microsoft=account, summary=summarized_email_content, calendar=summarized_calendar_task)
                        print("Summarization create successfully with calendar event")
                        for event in summarized_calendar_task:
                            response = create_calendar_event(access_token, event)
                            if response.status_code not in (200, 201):
                                print("Error creating calender events")
                            else:
                                print("Calender events created successfully")

                
                    time.sleep(1)
    
@shared_task 
def new_user_mail_sync(access_token, account):
    account = MicrosoftConnectedAccounts.objects.get(id=account)
    
    minutes_ago = datetime.now(timezone.utc) - timedelta(days=30)
    time_filter = minutes_ago.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    
    status_code, response = get_mail_messages(access_token, time_filter)
    
    response = response.json()
    
    values = response.get('value')
    if values:
        for value in values:
            email_payload = {}
            message_id = value.get('id')

            message = EmailMessages.objects.filter(message_id=message_id).first()
            if message:
                continue

            print("############################################")
            print(value)

            conversation_id = value.get('conversationId')
            email_payload['message_id'] = value.get('id')
            email_payload['subject'] = value.get('subject')
            email_payload['conversation_id'] = conversation_id
            conversation = EmailMessages.objects.filter(conversation_id=conversation_id, microsoft=account).first()
            email_payload['body_preview'] = value.get('bodyPreview')
            email_payload['content'] = value['body']['content']
            sender = ""
            sender = value.get('sender')
            if sender:
                email_payload['sender_email'] = sender['emailAddress']['address']
            to_recipients = value.get('toRecipients')
            email_payload['mail_time'] = value.get('createdDateTime')
            to_recipient_emails = []
            if to_recipients:
                for to_recipient in to_recipients:
                    to_recipient_email = to_recipient['emailAddress']['address']
                    to_recipient_emails.append(to_recipient_email)
            email_payload['to_recipient_emails'] = to_recipient_emails
            
            email: EmailMessages = EmailMessages.objects.create(**email_payload, microsoft=account)
            summarized_content = summarize_email_content(email_content=email.content, subject=email.subject)
            summarized_email_content = summarized_content.get("summary")
            summarized_calendar_task = summarized_content.get("calendar", None)
            if not summarized_calendar_task:
                summarization = Summarization.objects.create(email=email, microsoft=account, summary=summarized_email_content)
                print("summarization created successfully with not calendar event")
            else:
                summarization = Summarization.objects.create(email=email, microsoft=account, summary=summarized_email_content, calendar=summarized_calendar_task)
                print("Summarization create successfully with calendar event")
                for event in summarized_calendar_task:
                    response = create_calendar_event(access_token, event)
                    if response.status_code not in (200, 201):
                        print("Error creating calender events")
                    else:
                        print("Calender events created successfully")

            time.sleep(1)
