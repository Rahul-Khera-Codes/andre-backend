from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone as django_timezone

class UserToken(models.Model):
    access_token = models.CharField()
    created = models.DateTimeField(auto_now_add=True)
    microsoft = models.OneToOneField("MicrosoftConnectedAccounts", on_delete=models.CASCADE, related_name='user_token')
    refresh_token = models.CharField()
    updated = models.DateTimeField(auto_now=True)
    

class MicrosoftConnectedAccounts(models.Model):
    access_token = models.TextField(null=False)
    display_name =  models.CharField( null=True)
    given_name = models.CharField(null=False, blank=False)
    mail_id = models.CharField(null=False, blank=False)
    microsoft_id = models.CharField(null=False, blank=False)
    refresh_token = models.TextField(null=False)
    surname = models.CharField(null=True)
    user_principal_name = models.CharField(null=False, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class EmailMessages(models.Model):
    body_preview = models.CharField(null=False)
    content = models.CharField(null=False)
    conversation_id = models.CharField(null=True)
    folder_id = models.CharField()
    folder_name = models.CharField()
    mail_time = models.DateTimeField(null=True)
    message_id = models.CharField(null=False)
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.CASCADE, related_name="email_message")
    sender_email = models.CharField(null=True)
    subject = models.CharField(blank=True, null=True)
    to_recipient_emails = ArrayField(models.CharField(null=True), default=list)
    unique_body = models.CharField(blank=True, null=False)
    reply = models.CharField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class Summarization(models.Model):
    email = models.ForeignKey(EmailMessages, on_delete=models.CASCADE, blank=True, null=True, related_name="summarization")
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.CASCADE, related_name="summarization")
    summary = models.CharField(null=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    

class Calender(models.Model):
    body = models.CharField(null=True, blank=True)
    event_id = models.CharField()
    end = models.DateTimeField()
    email = models.ForeignKey(EmailMessages, on_delete=models.CASCADE, blank=True, null=True, related_name="calendar")
    location = models.CharField(blank=True, null=True)
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.CASCADE, related_name="calendar")
    remainder_minutes_before_start = models.IntegerField()
    start = models.DateTimeField()
    subject = models.CharField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    