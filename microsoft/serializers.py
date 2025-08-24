from rest_framework import serializers
from .models import (
    Calender,
    EmailMessages,
    MicrosoftConnectedAccounts,
    Summarization
)


class MicrosoftConnectAccountSerializer(serializers.ModelSerializer):
    # access_token = serializers.CharField()
    # display_name = serializers.CharField()
    # given_name = serializers.CharField()
    # id = serializers.IntegerField()
    # mail_id = serializers.CharField()
    # microsoft_id = serializers.CharField()
    # refresh_token = serializers.CharField()
    # surname = serializers.CharField()
    # user_principal_name = serializers.CharField()
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


class CalenderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calender
        fields = (
            "end",
            "email",
            "event_id",
            "location",
            "microsoft",
            "remainder",
            "start",
            "subject"
            "summary",
        )
        
    def to_representation(self, instance):
        return {
            "body": {
                "contentType": "html",
                "content": ""
            },
            "email_id": instance.email.message_id,
            "summary_id": instance.summary.id,
            "microsoft_id": instance.microsoft.microsoft_id,
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
        
class CalenderCreateSerializer(serializers.Serializer):
    end = serializers.DateTimeField()
    start = serializers.DateTimeField()
    subject = serializers.CharField()
    body = serializers.CharField(required=False, default="")
    location = serializers.CharField(required=False, default="")
    remainderMinutesBeforeStart = serializers.IntegerField(default=15, required=False)
    

class SummarizationSerializer(serializers.ModelSerializer):
    summary = serializers.CharField()
    calendar = CalenderSerializer(many=True, read_only=True)
    
    class Meta:
        model = Summarization
        fields = ("summary", "calendar")
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data
    
    
class EmailMessageSerializer(serializers.ModelSerializer):
    summarization = SummarizationSerializer(many=True, read_only=True)
    
    class Meta:
        model = EmailMessages
        fields = (
            "body_preview",
            "content",
            "conversation_id",
            "mail_time",
            "message_id",
            "microsoft",
            "sender_email",
            "subject",
            "summarization",
            "to_recipient_emails"
        )