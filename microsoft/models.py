from django.db import models
from django.contrib.postgres.fields import ArrayField


class MicrosoftConnectedAccounts(models.Model):
    microsoft_id = models.CharField(null=False, blank=False)
    user_principal_name = models.CharField(null=False, blank=False)
    mail_id = models.CharField(null=False, blank=False)
    display_name =  models.CharField( null=True)
    surname = models.CharField(null=True)
    given_name = models.CharField(null=False, blank=False)
    access_token = models.TextField(null=False)
    refresh_token = models.TextField(null=False)


class EmailMessages(models.Model):
    message_id = models.CharField(null=False)
    body_preview = models.CharField(null=False)
    subject = models.CharField(null=False)
    content = models.CharField(null=False)
    sender_email = models.CharField(null=True)
    to_recipient_emails = ArrayField(models.CharField(null=True), default=list)
    conversation_id = models.CharField(null=True)
    mail_time = models.DateTimeField(null=True)
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.CASCADE)


class Summarization(models.Model):
    email = models.ForeignKey(EmailMessages, on_delete=models.CASCADE, blank=True, null=True)
    calendar = models.JSONField(blank=True, null=True)
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.CASCADE)
    summary = models.CharField(null=False)