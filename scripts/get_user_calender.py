import os
import json

from dotenv import load_dotenv
import requests

load_dotenv()

# Replace with your valid access token
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
# print(ACCESS_TOKEN)

# Microsoft Graph endpoint for events
GRAPH_URL = "https://graph.microsoft.com/v1.0/me/events?$select=subject,start,end,reminderMinutesBeforeStart"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

response = requests.get(GRAPH_URL, headers=headers)

if response.status_code == 200:
    events = response.json().get("value", [])
    print("Upcoming events:")
    for event in events:
        print(json.dumps(event, indent=4))
        subject = event.get("subject", "No Title")
        start = event["start"]["dateTime"]
        end = event["end"]["dateTime"]
        reminder = event.get("reminderMinutesBeforeStart", None)
        print(f"- {subject} | {start} → {end} | Reminder: {reminder} mins before")
        print('-'*30)
else:
    print("Error:", response.status_code, response.text)
