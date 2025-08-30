
from datetime import (
    datetime,
    timedelta,
    time,
    timezone,
)
from traceback import format_exc

from asgiref.sync import sync_to_async
from adrf.views import APIView as AsyncAPIView
from django.utils import timezone as django_timezone
from django.db.models import QuerySet
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from ..models import EmailMessages, Calender
from ..serializers import EmailMessageSerializer, CalenderSerializer
from ..utils.auth import verify_access_token


async def latest_mails(account):
    emails = EmailMessages.objects.filter(microsoft=account)
    folder_name = emails.values_list("folder_name", flat=True).distinct()
    latest_folder_mails = (
        EmailMessages.objects.filter(folder_name__in=folder_name)
        .order_by("folder_name", "-created")
        .distinct('folder_name')
    )
    return latest_folder_mails
    
async def latest_calender_events(account):
    now = django_timezone.now()
    start_dt = datetime.combine(now.date(), time=time.min)
    end_dt = datetime.combine(now.date(), time=time.max)
    events = Calender.objects.filter(microsoft=account, start__gt=start_dt, end__lte=end_dt)
    
    # events = Calender.objects.filter(microsoft=request.user, start__gt=now, end__lte=end_dt)
    # events_len = len(events)
    # events_len = events_len if events_len > 5 else 5
    # serializer_calender = CalenderSerializer(events[events_len:], many=True)
    
    return events
class DashboardView(AsyncAPIView):
    permission_classes = [IsAuthenticated]
    
    async def get(self, request):
        try:
            # latest emails from each folder
            
            latest_folder_mails = await latest_mails(request.user)
            serializer_email = EmailMessageSerializer(latest_folder_mails, many=True)
            
            # all todays events        
            events = await latest_calender_events(account=request.user)
            serializer_calendar = CalenderSerializer(events, many=True)
            
            serializer_email_data = await sync_to_async(lambda: serializer_email.data, thread_sensitive=False)()
            serializer_calendar_data = await sync_to_async(lambda: serializer_calendar.data, thread_sensitive=False)()
            
            data = {
                "emails": serializer_email_data,
                "events": serializer_calendar_data
            } 
            
            return Response(data, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(format_exc())
            return Response({"error": "Internal Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
    
    