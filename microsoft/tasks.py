import json, time
from celery import shared_task
from datetime import date, datetime, timedelta, timezone
from .models import MicrosoftConnectedAccounts, EmailMessages
from .utils import get_mail_messages, get_refresh_token

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
                    conversation = EmailMessages.objects.filter(conversation_id=conversation_id, microsoft=account).first()
                    
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
    
                    email = EmailMessages.objects.create(**email_payload, microsoft=account)
                    email_message_id = email
                    # knowledge_base_embedding_and_storage(account.user, json.dumps(email_payload))
                    time.sleep(5)
                    email_payload['mail_account_holder'] = account.mail_id
                    email_payload['current_date'] = str(date.today())
                    email_payload.pop("mail_time")
                    email_payload.pop("conversation_id")

                    # graph = graph_initialisation()
                    # if conversation_id and conversation:
                    #     response = trail_mail_graph_invoke(json.dumps(email_payload), graph)
                    # else:
                    #     response = graph_invoke(json.dumps(email_payload), graph)

                    # response = json.loads(response)
                
                    # if response != False:
                    #     for task in response:
                    #         TodoTasks.objects.create(**task, task_creation_type="automatic",  mail_message=email_message_id, user=account.user)
    
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

            email_payload['message_id'] = value.get('id')
            email_payload['subject'] = value.get('subject')
            conversation_id = value.get('conversationId')
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
            
            email = EmailMessages.objects.create(**email_payload, microsoft=account)
            email_message_id = email
            email_payload['mail_account_holder'] = account.mail_id
            email_payload['current_date'] = str(date.today())
            email_payload.pop("mail_time")
            email_payload.pop("conversation_id")
            
            time.sleep(5)
            # graph = graph_initialisation()
            # if conversation_id and conversation:
            #     response = trail_mail_graph_invoke(json.dumps(email_payload), graph)
            # else:
            #     response = graph_invoke(json.dumps(email_payload), graph)
    
            # response = json.loads(response)
        
            # if response != False:
            #     TodoTasks.objects.create(**response, task_creation_type="automatic", mail_message=email_message_id, user=account.user)

