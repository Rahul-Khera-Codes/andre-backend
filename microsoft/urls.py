from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    GetConnectedAccounts,
    GetUserMail,
    MicrosoftConnectVerify, 
)
from .views.auth import RefreshTokenView
from .views.calendar import CalenderEventView

urlpatterns = [
    path('oauth/outlook/callback/', MicrosoftConnectVerify.as_view(), name='outlook_oauth'),
    path('get/microsoft/accounts', GetConnectedAccounts.as_view(), name='get_microsoft_accounts'),
    path("get/mails/", GetUserMail.as_view(), name="get_user_mail"),
    path("auth/refresh/", RefreshTokenView.as_view(), name="auth_refresh_token"),
    path("calender", CalenderEventView.as_view(), name='calender_event')
]