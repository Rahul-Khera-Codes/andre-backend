
from datetime import (
    datetime,
    timedelta,
    time,
    timezone,
)
from traceback import format_exc

from django.utils import timezone as django_timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from ..models import EmailMessages, Calender
from ..serializers import EmailMessageSerializer, CalenderSerializer
from ..utils.auth import verify_access_token


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # latest emails from each folder
            emails = EmailMessages.objects.filter(microsoft=request.user)
            folder_name = emails.values_list("folder_name", flat=True).distinct()
            latest_folder_mails = (
                EmailMessages.objects.filter(folder_name__in=folder_name)
                .order_by("folder_name", "-created")
                .distinct('folder_name')
            )
            serializer_email = EmailMessageSerializer(latest_folder_mails, many=True)
            
            # all todays events    
            now = django_timezone.now()
            start_dt = datetime.combine(now.date(), time=time.min)
            end_dt = datetime.combine(now.date(), time=time.max)
        
            events = Calender.objects.filter(microsoft=request.user, start__gt=start_dt, end__lte=end_dt)
            # events = Calender.objects.filter(microsoft=request.user, start__gt=now, end__lte=end_dt)
            # events_len = len(events)
            # events_len = events_len if events_len > 5 else 5
            # serializer_calender = CalenderSerializer(events[events_len:], many=True)
            serializer_calender = CalenderSerializer(events, many=True)
            
            data = {
                "emails": serializer_email.data,
                "events": serializer_calender.data
            } 
            
            return Response(data, status=status.HTTP_200_OK)
        
        except Exception as e:
            print(format_exc())
            return Response({"error": "Internal Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
    
    