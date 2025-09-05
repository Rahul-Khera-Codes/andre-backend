from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone as django_timezone
from django.utils.translation import gettext_lazy as _

class UserToken(models.Model):
    access_token = models.CharField()
    created = models.DateTimeField(auto_now_add=True)
    microsoft = models.OneToOneField("MicrosoftConnectedAccounts", on_delete=models.CASCADE, related_name='user_token')
    refresh_token = models.CharField()
    updated = models.DateTimeField(auto_now=True)
    

class MicrosoftConnectedAccounts(models.Model):
    access_token = models.TextField(null=False)
    container_name = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    display_name =  models.CharField( null=True)
    given_name = models.CharField(null=False, blank=False)
    mail_id = models.CharField(null=False, blank=False)
    microsoft_id = models.CharField(null=False, blank=False)
    refresh_token = models.TextField(null=False)
    surname = models.CharField(null=True)
    user_principal_name = models.CharField(null=False, blank=False)
    updated = models.DateTimeField(auto_now=True)
    
    @property
    def is_authenticated(self):
        """Always return True for authenticated Microsoft accounts."""
        return True

    @property
    def is_anonymous(self):
        """For compatibility with Django's auth system."""
        return False

    def __str__(self):
        return self.mail_id


class EmailMessages(models.Model):
    attachment_ids = ArrayField(models.TextField(null=True), default=list)
    attachment_content_type = models.CharField(null=True, blank=True)
    bcc_recipients = ArrayField(models.CharField(null=True), default=list)
    body_preview = models.CharField(null=False)
    cc_recipients = ArrayField(models.CharField(null=True), default=list)
    content = models.CharField(null=False)
    conversation_id = models.CharField(null=True)
    folder_id = models.CharField()
    folder_name = models.CharField()
    has_attachments = models.BooleanField(default=False)
    mail_time = models.DateTimeField(null=True)
    message_id = models.CharField(null=False, unique=True)
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.CASCADE, related_name="email_message")
    received_date_time = models.DateTimeField()
    reply = models.CharField(blank=True, null=True)
    reply_id = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="draft_message"
    )
    send_date_time = models.DateTimeField()
    sender_email = models.CharField(null=True)
    subject = models.CharField(blank=True, null=True)
    to_recipient_emails = ArrayField(models.CharField(null=True), default=list)
    unique_body = models.CharField(blank=True, null=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


# class Documents(models.Model):
#     microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.CASCADE, related_name="documents")
#     content_type = models.CharField(blank=True, null=True)
#     document_ids = 


class SummarizationChoices(models.TextChoices):
    EMAIL = "EML", _("Email")
    EMAIL_ATTACHMENT = "EMA", _("Attachments")
    DOCUMENts = "DOC", _("Documents")

class Summarization(models.Model):
    email = models.ForeignKey(EmailMessages, on_delete=models.CASCADE, blank=True, null=True, related_name="summarization")
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.CASCADE, related_name="summarization")
    summary = models.CharField(null=False)
    summary_type = models.CharField(max_length=3, choices=SummarizationChoices, default=SummarizationChoices.EMAIL)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    

class Calender(models.Model):
    body = models.CharField(null=True, blank=True)
    end = models.DateTimeField()
    email = models.ForeignKey(EmailMessages, on_delete=models.CASCADE, blank=True, null=True, related_name="calendar")
    event_id = models.CharField()
    location = models.CharField(blank=True, null=True)
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.CASCADE, related_name="calendar")
    remainder_minutes_before_start = models.IntegerField()
    start = models.DateTimeField()
    subject = models.CharField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    
class VectorStore(models.Model):
    vector_store_id = models.CharField(max_length=64, unique=True, blank=True, null=True)
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.SET_NULL, null=True, related_name="vector_store")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.vector_store_id} ({self.client_id})"


class Session(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    microsoft = models.ForeignKey(MicrosoftConnectedAccounts, on_delete=models.SET_NULL, related_name="session", null=True)
    session_id = models.CharField(max_length=64, unique=True)
    session_name = models.CharField(default='Demo chat')
    vector_store = models.ForeignKey(VectorStore, on_delete=models.CASCADE, related_name='sessions', blank=True, null=True)

    def __str__(self):
        return self.session_id
    


class Message(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=16, choices=[('user', 'User'), ('assistant', 'Assistant')])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content
        }

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}"