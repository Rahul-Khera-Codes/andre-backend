from datetime import datetime, timezone
from typing import Literal

from adrf import serializers as async_serializers
from rest_framework import serializers
from ..models import (
    Calender,
    EmailMessages,
    MicrosoftConnectedAccounts,
    Summarization
)


class MicrosoftConnectAccountSerializerAsync(async_serializers.ModelSerializer):
    class Meta:
        model = MicrosoftConnectedAccounts
        fields = (
            "display_name",
            "given_name",
            "id",
            "mail_id",
            "microsoft_id",
            "surname",
            "user_principal_name"
        )


class CalenderSerializerAsync(async_serializers.ModelSerializer):
    class Meta:
        model = Calender
        fields = (
            "end",
            "email",
            "event_id",
            "location",
            "microsoft",
            "remainder_minutes_before_start",
            "start",
            "subject"
        )
        
    async def ato_representation(self, instance):
        return {
            "body": {
                "contentType": "html",
                "content": ""
            },
            "email_id": instance.email.message_id if hasattr(instance.email, "message_id")  else None,
            # "summary_id": instance.summary.id if hasattr(instance.summary, "id") else None,
            # "microsoft_id": instance.microsoft.microsoft_id,
            "event_id": instance.event_id,
            "reminderMinutesBeforeStart": instance.remainder_minutes_before_start,
            "subject": instance.subject,
            "start": {
                "dateTime": instance.start,
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": instance.end,
                "timeZone": "UTC"
            },
            "location": {
                "displayName": instance.location
            }
        }
        
        
class CalenderCreateSerializerAsync(async_serializers.Serializer):
    end = serializers.DateTimeField()
    start = serializers.DateTimeField()
    subject = serializers.CharField(required=False, default="")
    body = serializers.CharField(required=False, default="")
    location = serializers.CharField(required=False, default="")
    remainderMinutesBeforeStart = serializers.IntegerField(default=15, required=False)
    

class SummarizationSerializerAsync(async_serializers.ModelSerializer):
    summary = serializers.CharField()
    calendar = CalenderSerializerAsync(many=True, read_only=True)
    
    class Meta:
        model = Summarization
        fields = ("summary", "calendar")
    
    async def ato_representation(self, instance):
        data = super().to_representation(instance)
        return data
    
    
class EmailMessageSerializerAsync(async_serializers.ModelSerializer):
    summarization = SummarizationSerializerAsync(many=True, read_only=True)
    
    class Meta:
        model = EmailMessages
        fields = (
            "bcc_recipients",
            "body_preview",
            "cc_recipients",
            "content",
            "conversation_id",
            "folder_id",
            "folder_name",
            "mail_time",
            "message_id",
            "microsoft",
            "reply",
            "sender_email",
            "subject",
            "summarization",
            "to_recipient_emails",
            "received_date_time",
            "send_date_time",
        )
        
        
class RefreshTokenSerailizerAsync(async_serializers.Serializer):
    token = serializers.CharField()
    
class DraftSerializerAsync(async_serializers.Serializer):
    filter = serializers.CharField()
    body = serializers.CharField()
    recipients = serializers.ListField(child=serializers.CharField(), required=False, default=[])
    subject = serializers.CharField(required=False, default='')
    

class DocumentSerializerAsync(async_serializers.Serializer):
    file_type = serializers.CharField()
    document = serializers.FileField()