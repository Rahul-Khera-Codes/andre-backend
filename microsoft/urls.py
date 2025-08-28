from django.urls import path

from rest_framework_simplejwt.views import TokenRefreshView

from .views.dashboard import DashboardView
from .views.email import (
    GetUserMail,
    GetMailFolder
)
from .views.auth import (
    GetConnectedAccounts,
    MicrosoftConnectVerify,
    RefreshTokenView
)
from .views.calendar import (
    CalenderEventView, 
    CalenderEventNotificationView
)

urlpatterns = [
    path("dashboard/", DashboardView.as_view(), name='dashboard'),
    path('oauth/outlook/callback/', MicrosoftConnectVerify.as_view(), name='outlook_oauth'),
    path('get/microsoft/accounts', GetConnectedAccounts.as_view(), name='get_microsoft_accounts'),
    path("get/mails/", GetUserMail.as_view(), name="get_user_mail"),
    path('get/mail/folder/', GetMailFolder.as_view(), name='get_user_mail_folders'),
    path("auth/refresh/", RefreshTokenView.as_view(), name="auth_refresh_token"),
    path("calendar/", CalenderEventView.as_view(), name='calender_event'),
    path("calendar/notification/", CalenderEventNotificationView.as_view(), name='calender_event_notification')
]