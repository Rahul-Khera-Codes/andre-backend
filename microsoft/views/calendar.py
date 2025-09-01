from datetime import (
    datetime,
    timedelta, 
    timezone
)
from traceback import format_exc
import uuid

from adrf.views import APIView as AsyncAPIView
from asgiref.sync import sync_to_async
from django.utils import timezone as django_timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


from ..utils.auth import verify_access_token
from ..models import Calender
from ..serializers import (
    CalenderSerializer,
    CalenderCreateSerializer
)
from ..serializers.aserializers import (
    CalenderSerializerAsync,
    CalenderCreateSerializerAsync
)
from ..utils import create_calendar_event



class CalenderEventView(AsyncAPIView):
    permission_classes = [IsAuthenticated]
    
    async def get(self, request):
        try:
            now = django_timezone.now()
            # thresold = now + timezone(minutes=15)
            events = Calender.objects.filter(microsoft=request.user, start__gt=now)
            serializer = CalenderSerializerAsync(events, many=True)
            # serializer_data = await sync_to_async(lambda: serializer.data)()
            # return Response(serializer_data, status=status.HTTP_200_OK)
            serializer_data = await serializer.adata
            return Response(serializer_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(format_exc())
            return Response({"error": "Internal Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    
    
    
    async def post(self, request):
        try:
                
            serializers = CalenderCreateSerializer(data=request.data)
            if serializers.is_valid():
                event_body = {
                    'subject': serializers.validated_data.get('subject'),
                    'start': {
                        "dateTime": serializers.validated_data.get('start'),
                        "timeZone": "UTC"
                    },
                    'end': {
                        "dateTime": serializers.validated_data.get('end'),
                        "timeZone": "UTC"
                    },
                    "reminderMinutesBeforeStart": serializers.validate_data.get('reminderMinutesBeforeStart'),
                }
                body = serializers.validated_data.get('body')
                location = serializers.validated_data.get('location')
                if body:
                    event_body['body'] = body
                if location: event_body['location'] = location
                
                status_code, response = await sync_to_async(lambda: create_calendar_event(request.user.access_token, event_body))()
                if status_code not in (200, 201):
                    return Response({"error": "Error in creating calender event"}, status=status.HTTP_400_BAD_REQUEST)
                
                event_body = {
                    "event_id": response.get('id'),
                    'subject': response.get('subject'),
                    'start': response.get('start'),
                    'end': response.get('end'),
                    "reminderMinutesBeforeStart": response.get('reminderMinutesBeforeStart'),
                }
                body = response.get('body')
                location = response.get('location')
                if body:
                    event_body['body'] = body
                if location: event_body['location'] = location
                
                calender = Calender.objects.acreate(**event_body, microsoft=request.user)
                return Response({"message": "Calendar event created successfully"}, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({"error": "Internal Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    


async def generate_dummy_events():
    events = []
    now_utc = datetime.now(timezone.utc)

    for i in range(3):
        start_time = now_utc + timedelta(minutes=5 * (i + 1))
        end_time = start_time + timedelta(minutes=30)

        event = {
            "id": str(uuid.uuid4()),
            "subject": f"Dummy Event {i+1}",
            "bodyPreview": "This is a test event generated for demo purposes.",
            "start": {
                "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "timeZone": "UTC"
            },
            "location": {
                "displayName": "Online"
            }
        }
        events.append(event)

    return events

        
class CalenderEventNotificationView(AsyncAPIView):
    permission_classes = [IsAuthenticated]
    
    async def get(self, request):
        try:
            # print("\nAnonymous user:", request.user)
            now = django_timezone.now()
            thresold = now + timedelta(minutes=15)
            events = await sync_to_async(
                lambda: Calender.objects.filter(microsoft=request.user, start__gt=now, start__lte=thresold),
                thread_sensitive=False
            )()
            
            if (await sync_to_async(lambda: len(events), thread_sensitive=False)()) == 0:
                events = await generate_dummy_events()
                return Response(events, status=status.HTTP_200_OK)
            
            else:
                serializer = CalenderSerializerAsync(events, many=True)
                return Response(serializer.adata, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(format_exc())
            return Response({"error": f"Internal Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    