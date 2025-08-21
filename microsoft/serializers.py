from rest_framework import serializers

class MicrosoftConnectAccountSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    display_name = serializers.CharField()
    given_name = serializers.CharField()
    id = serializers.IntegerField()
    microsoft_id = serializers.CharField()
    mail = serializers.CharField()
    refresh_token = serializers.CharField()
    surname = serializers.CharField()
    user_principal_name = serializers.CharField()