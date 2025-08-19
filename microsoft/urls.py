from django.urls import path
from .views import (MicrosoftConnectVerify, GetConnectedAccounts)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('oauth/outlook/callback/', MicrosoftConnectVerify.as_view(), name='outlook_oauth'),
    path('get/microsoft/accounts', GetConnectedAccounts.as_view(), name='get_microsoft_accounts'),
]