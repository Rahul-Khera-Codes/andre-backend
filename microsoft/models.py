from django.db import models
from django.contrib.postgres.fields import ArrayField


class MicrosoftConnectedAccounts(models.Model):
    access_token = models.TextField(null=False)
    display_name =  models.CharField( null=True)
    given_name = models.CharField(null=False, blank=False)
    mail_id = models.CharField(null=False, blank=False)
    microsoft_id = models.CharField(null=False, blank=False)
    refresh_token = models.TextField(null=False)
    surname = models.CharField(null=True)
    user_principal_name = models.CharField(null=False, blank=False)


class EmailMessages(models.Model):
    body_preview = models.CharField(null=False)
    content = models.CharField(null=False)
    conversation_id = models.CharField(null=True)
    mail_time = models.DateTimeField(null=True)
    message_id = models.CharField(null=False)
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.CASCADE, related_name="email_message")
    sender_email = models.CharField(null=True)
    subject = models.CharField(null=False)
    to_recipient_emails = ArrayField(models.CharField(null=True), default=list)
    unique_body = models.CharField(null=False)


class Summarization(models.Model):
    email = models.ForeignKey(EmailMessages, on_delete=models.CASCADE, blank=True, null=True, related_name="summarization")
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.CASCADE, related_name="summarization")
    summary = models.CharField(null=False)
    

class Calender(models.Model):
    body = models.CharField(null=True, blank=True)
    event_id = models.CharField()
    end = models.DateTimeField()
    email = models.ForeignKey(EmailMessages, on_delete=models.CASCADE, blank=True, null=True, related_name="calendar")
    location = models.CharField(blank=True, null=True)
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.CASCADE, related_name="calendar")
    remainder_minutes_before_start = models.IntegerField()
    summary = models.ForeignKey(Summarization, on_delete=models.CASCADE, blank=True, null=True, related_name="calendar")
    start = models.DateTimeField()
    subject = models.CharField()