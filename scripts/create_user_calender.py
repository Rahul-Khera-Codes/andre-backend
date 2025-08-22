import os

from dotenv import load_dotenv
import requests

load_dotenv()

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

url = "https://graph.microsoft.com/v1.0/me/events"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

event =  {
            "subject": "Team Meeting",
            "body": {
                "contentType": "HTML",
                "content": "Meeting scheduled at 12pm on August 22, 2025."
            },
            "start": {
                "dateTime": "2025-08-22T12:00:00",
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": "2025-08-22T13:00:00",
                "timeZone": "UTC"
            },
            "location": {
                "displayName": ""
            },
            "reminderMinutesBeforeStart": 15
        }

response = requests.post(url, headers=headers, json=event)

if response.status_code in (200, 201):
    print("Event created successfully!")
    print(response.json())
else:
    print("Error:", response.status_code, response.text)
