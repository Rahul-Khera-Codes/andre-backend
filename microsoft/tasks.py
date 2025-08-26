import json, time
from datetime import (
    date, 
    datetime, 
    timedelta, 
    timezone
)
from traceback import format_exc

from celery import shared_task
# from django.core.mail import send_mail
from django.utils import timezone as django_timezone

from .graph import summarize_email_content
from .models import (
    Calender,
    EmailMessages, 
    MicrosoftConnectedAccounts, 
    Summarization
)
from .utils import (
    create_calendar_event,
    get_calendar_event,
    get_folder_map,
    get_mail_messages,
    get_mail_messages_loop_all,
    get_refresh_token,
    get_unique_body,
    send_mail
)
from .exceptions import MSInvalidTokenError


@shared_task
def mail_retrieve():
    
    accounts = MicrosoftConnectedAccounts.objects.all()
    if accounts:
        try:
            for account in accounts:
                access_token = account.access_token
                refresh_token = account.refresh_token
                
                folder_mapping: dict | None = None
                try:
                    folder_mapping = get_folder_map(access_token=access_token)
                except MSInvalidTokenError as e:
                    status_code, response = get_refresh_token(refresh_token)
                    
                    if status_code != 200:
                        raise MSInvalidTokenError('Microsoft token expired, please login again')
                    
                    response = response.json()
                    access_token = response.get('access_token')
                    refresh_token = response.get('refresh_token')
                    account.access_token  = access_token
                    account.refresh_token = refresh_token
                    account.save()
                    
                    folder_mapping = get_folder_map(access_token=access_token)
                
                
                minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
                time_filter = minutes_ago.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                status_code, response = get_mail_messages(access_token, time_filter)
                
                if status_code != 200:
                    status_code, response = get_refresh_token(refresh_token)
                    
                    if status_code != 200:
                        raise MSInvalidTokenError('Microsoft token expired, please login again')
                    
                    response = response.json()
                    access_token = response.get('access_token')
                    refresh_token = response.get('refresh_token')
                    account.access_token  = access_token
                    account.refresh_token = refresh_token
                    account.save()
                    
                    status_code, response = get_mail_messages(access_token, time_filter)
                    
                    if status_code != 200:
                        raise MSInvalidTokenError('Microsoft token expired, please login again')
                    
                response = response.json()

                values = response.get('value')[::-1]
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
                        
                        folder_id = value.get('parentFolderId')
                        email_payload['folder_id'] = folder_id
                        email_payload['folder_name'] = folder_mapping.get(folder_id)
                        
                        email_payload['message_id'] = value.get('id')
                        email_payload['subject'] = value.get('subject')
                        email_payload['body_preview'] = value.get('bodyPreview')
                        email_payload['content'] = value['body']['content']
                        email_payload['unique_body'] = get_unique_body(value['uniqueBody'])
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
                        
                        # if value.get('from').get('emailAddress').get("address") == account.mail_id: continue
                            
                        summarized_content = summarize_email_content(email_content=email.unique_body, subject=email.subject)
                        summarized_email_content = summarized_content.get("summary")
                        summarized_calendar_task = summarized_content.get("calendar", None)
                        summarized_email_reply = summarized_content.get('reply')
                        
                        email.reply = summarized_email_reply
                        email.save()
                        
                        summarization = Summarization.objects.create(email=email, microsoft=account, summary=summarized_email_content)
                        
                        if summarized_calendar_task:
                            
                            print("Summarization create successfully with calendar event")
                            for event in summarized_calendar_task:
                                status_code, response = create_calendar_event(access_token, event)
                                if status_code not in (200, 201):
                                    print("Error creating calender events")
                                else:
                                    event_payload = {}
                                    event_id = response.get('id')
                                    event_payload['event_id'] = event_id
                                    event_payload['subject'] = response.get('subject')
                                    event_payload['start'] = response.get('start').get("dateTime")
                                    event_payload['end'] = response.get('end').get("dateTime")
                                    body = response.get("body")
                                    if body:
                                        event_payload['body'] = body
                                    event_payload['remainder_minutes_before_start'] = response['reminderMinutesBeforeStart']
                                    # print("Event payload", event_payload)
                                    event: Calender = Calender.objects.create(**event_payload, microsoft=account)
                                    print("Calender events created successfully")
                    
                        time.sleep(1)
                        
        except MSInvalidTokenError as e:
            print("Microsoft token expired please login")


@shared_task
def calendar_event_retrieve():
    
    accounts = MicrosoftConnectedAccounts.objects.all()
    if accounts:
        try:
            for account in accounts:
                access_token = account.access_token
                refresh_token = account.refresh_token
                minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
                time_filter = minutes_ago.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
                status_code, response = get_calendar_event(access_token, time_filter)
                
                if status_code != 200:
                    status_code, response = get_refresh_token(refresh_token)
                    
                    if status_code != 200:
                        raise MSInvalidTokenError('Microsoft token expired, please login again')
                    
                    response = response.json()
                    access_token = response.get('access_token')
                    refresh_token = response.get('refresh_token')
                    account.access_token  = access_token
                    account.refresh_token = refresh_token
                    account.save()
                    
                    status_code, response = get_calendar_event(access_token, time_filter)
                    
                    if status_code != 200:
                        raise MSInvalidTokenError('Microsoft token expired, please login again')
                    
                response = response.json()

                values = response.get('value')
                if values:
                    for value in values:
                        # print("Retreived calender:", value)
                        event_payload = {}
                        event_id = value.get('id')
        
                        event = Calender.objects.filter(event_id=event_id, microsoft=account).first()
                        if event:
                            continue
                        
                        event_payload['event_id'] = event_id
                        event_payload['subject'] = value.get('subject')
                        event_payload['start'] = value.get('start').get("dateTime")
                        event_payload['end'] = value.get('end').get("dateTime")
                        body = value.get("body")
                        if body:
                            event_payload['body'] = body
                        event_payload['remainder_minutes_before_start'] = value['reminderMinutesBeforeStart']
                        # print("Event payload", event_payload)
                        event: Calender = Calender.objects.create(**event_payload, microsoft=account)
                        
                        print("Event saved in database successfully")
                    
                        time.sleep(1)
        except MSInvalidTokenError as e:
            print(f"Error: {str(e)}")


@shared_task
def calender_email_notification():
    accounts = MicrosoftConnectedAccounts.objects.all()
    for account in accounts:
        now = django_timezone.now()
        thresold = now + timedelta(minutes=15)
        calendar = Calender.objects.filter(microsoft=account, start__gt=now, start__lte=thresold)
        
        for event in calendar:
            try:
                status_code, response = send_mail(
                    access_token=account.access_token,
                    subject=event.subject,
                    body=event.body,
                    to_recipient=account.mail_id
                )
                print(response)
                if status_code in (200, 201, 202):
                    print("Mail sended successfully")
                else:
                    print("Mail sending failed")
            except Exception as e:
                print(format_exc())
                print("Error sending mail:", str(e))

    
@shared_task 
def new_user_mail_sync(access_token, account):
    account = MicrosoftConnectedAccounts.objects.get(id=account)
    access_token = account.access_token
    refresh_token = account.refresh_token
    
    
    def get_messages(next_link: str | None = None) -> list:
        nonlocal access_token, refresh_token

        status_code, response = get_mail_messages(access_token, new_user=True)
        
        if status_code != 200:
            status_code, response = get_refresh_token(refresh_token)
            
            if status_code != 200:
                raise MSInvalidTokenError("Microsoft token expired please login again")
            
            response = response.json()
            access_token = response.get('access_token')
            refresh_token = response.get('refresh_token')
            account.access_token  = access_token
            account.refresh_token = refresh_token
            account.save()
            
            status_code, response = get_mail_messages(access_token, new_user=True)
            
            if status_code != 200:
                raise MSInvalidTokenError("Microsoft token expired please login again")
            
            
        response = response.json()
        values = response.get('value')
        
        return values
    
    
    try:            

        folder_mapping: dict | None = None
        try:
            folder_mapping = get_folder_map(access_token=access_token)
        except MSInvalidTokenError as e:
            status_code, response = refresh_token(refresh_token)
            
            if status_code != 200:
                raise MSInvalidTokenError('Microsoft token expired, please login again')
            
            response = response.json()
            access_token = response.get('access_token')
            refresh_token = response.get('refresh_token')
            account.access_token  = access_token
            account.refresh_token = refresh_token
            account.save()
            
            folder_mapping = get_folder_map(access_token=access_token)
        
        
        values = get_messages()
        
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
                
                folder_id = value.get('parentFolderId')
                email_payload['folder_id'] = folder_id
                email_payload['folder_name'] = folder_mapping.get(folder_id)
                
                email_payload['message_id'] = value.get('id')
                email_payload['subject'] = value.get('subject')
                email_payload['body_preview'] = value.get('bodyPreview')
                email_payload['content'] = value['body']['content']
                email_payload['unique_body'] = get_unique_body(value['uniqueBody'])
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
                
                summarized_content = summarize_email_content(email_content=email.unique_body, subject=email.subject)
                print(summarized_content)
                summarized_email_content = summarized_content.get("summary")
                summarized_calendar_task = summarized_content.get("calendar", None)
                summarized_email_reply = summarized_content.get("reply")
                
                # save generated mail reply
                email.reply = summarized_email_reply
                email.save()
                
                summarization = Summarization.objects.create(email=email, microsoft=account, summary=summarized_email_content)
                
                if summarized_calendar_task:
                    
                    print("Summarization create successfully with calendar event")
                    for event in summarized_calendar_task:
                        status_code, response = create_calendar_event(access_token, event)
                        
                        if status_code not in (200, 201):
                            print("Error creating calender events")
                        else:
                            event_payload = {}
                            event_id = response.get('id')
                            event_payload['event_id'] = event_id
                            event_payload['subject'] = response.get('subject')
                            event_payload['start'] = response.get('start').get("dateTime")
                            event_payload['end'] = response.get('end').get("dateTime")
                            body = response.get("body")
                            if body:
                                event_payload['body'] = body
                            event_payload['remainder_minutes_before_start'] = response['reminderMinutesBeforeStart']
                            # print("Event payload", event_payload)
                            event: Calender = Calender.objects.create(**event_payload, microsoft=account)
                            print("Calender events created successfully")
                    
            time.sleep(1)
            
    except MSInvalidTokenError as e:
        print(format_exc())    

    
@shared_task 
def new_user_mail_sync_all(access_token, account):
    account = MicrosoftConnectedAccounts.objects.get(id=account)
    access_token = account.access_token
    refresh_token = account.refresh_token
    
    def get_messages(next_link: str | None = None) -> list:
        nonlocal access_token, refresh_token
        
        minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=30)
        time_filter = minutes_ago.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        if next_link:
            status_code, response = get_mail_messages_loop_all(access_token, time_filter, next_link)
        else:
            status_code, response = get_mail_messages_loop_all(access_token, time_filter)
        
        if status_code != 200:
            status_code, response = get_refresh_token(refresh_token)
            
            if status_code != 200:
                raise MSInvalidTokenError("Microsoft token expired please login again")
            
            response = response.json()
            access_token = response.get('access_token')
            refresh_token = response.get('refresh_token')
            account.access_token  = access_token
            account.refresh_token = refresh_token
            account.save()
            
            status_code, response = get_mail_messages_loop_all(access_token, time_filter)
            
            if status_code != 200:
                raise MSInvalidTokenError("Microsoft token expired please login again")
            
            
        response = response.json()
        values = response.get('value')[::-1]
        next_link = response.get("@odata.nextLink")
        
        return values, next_link
    
    
    try:
        
        folder_mapping: dict | None = None
        try:
            folder_mapping = get_folder_map(access_token=access_token)
        except MSInvalidTokenError as e:
            status_code, response = refresh_token(refresh_token)
            
            if status_code != 200:
                raise MSInvalidTokenError('Microsoft token expired, please login again')
            
            response = response.json()
            access_token = response.get('access_token')
            refresh_token = response.get('refresh_token')
            account.access_token  = access_token
            account.refresh_token = refresh_token
            account.save()
            
            folder_mapping = get_folder_map(access_token=access_token)
        
            
        values, next_link  = get_messages()
        messages = [*values]
        not_next_link = False
        
        while len(messages) != 0:
            if not next_link:
                not_next_link = True
                
            for value in values:
                email_payload = {}
                message_id = value.get('id')

                message = EmailMessages.objects.filter(message_id=message_id, microsoft=account).first()
                if message:
                    continue
                
                conversation_id = value.get('conversationId')
                email_payload['conversation_id'] = conversation_id
                # conversation = EmailMessages.objects.filter(conversation_id=conversation_id, microsoft=account).first()
                
                folder_id = value.get('parentFolderId')
                email_payload['folder_id'] = folder_id
                email_payload['folder_name'] = folder_mapping.get(folder_id)
                
                email_payload['message_id'] = value.get('id')
                email_payload['subject'] = value.get('subject')
                email_payload['body_preview'] = value.get('bodyPreview')
                email_payload['content'] = value['body']['content']
                email_payload['unique_body'] = get_unique_body(value['uniqueBody'])
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
                
                summarized_content = summarize_email_content(email_content=email.unique_body, subject=email.subject)
                summarized_email_content = summarized_content.get("summary")
                summarized_calendar_task = summarized_content.get("calendar", None)
                summarized_email_reply = summarized_content.get("reply")
                
                email.reply = summarized_email_reply
                email.save()
                
                summarization = Summarization.objects.create(email=email, microsoft=account, summary=summarized_email_content)
                
                if summarized_calendar_task:
                    
                    print("Summarization create successfully with calendar event")
                    for event in summarized_calendar_task:
                        status_code, response = create_calendar_event(access_token, event)
                        
                        if status_code not in (200, 201):
                            print("Error creating calender events")
                        else:
                            event_payload = {}
                            event_id = response.get('id')
                            event_payload['event_id'] = event_id
                            event_payload['subject'] = response.get('subject')
                            event_payload['start'] = response.get('start').get("dateTime")
                            event_payload['end'] = response.get('end').get("dateTime")
                            body = response.get("body")
                            if body:
                                event_payload['body'] = body
                            event_payload['remainder_minutes_before_start'] = response['reminderMinutesBeforeStart']
                            # print("Event payload", event_payload)
                            event: Calender = Calender.objects.create(**event_payload, microsoft=account)
                            print("Calender events created successfully")
                            
            if not_next_link:
                break
            time.sleep(1)
            values, next_link = get_messages(next_link)
            messages.extend(values)
            
    except MSInvalidTokenError as e:
        print(format_exc())    
