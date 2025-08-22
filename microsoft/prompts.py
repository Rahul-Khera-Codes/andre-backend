
def generate_email_summary_and_events(email_content, subject):
    """
    Generates a prompt for email summarization and calendar event detection.
    Returns a structured prompt that can be sent to an LLM.
    """
    prompt = f"""
    Analyze the following email and provide a summary and extract any calendar events or todos.
    If there are no calendar events or todos, only include the summary in the response.

    Email Subject: {subject}
    Email Content: {email_content}

    Please provide your response in the following JSON format:
    {{
        "summary": "A concise summary of the email content",
        "calendar": [
            {{
                "subject": "The event title or task name",
                "body": {{
                    "contentType": "HTML",
                    "content": "Event description or details"
                }},
                "start": {{
                    "dateTime": "YYYY-MM-DDTHH:MM:SS",
                    "timeZone": "UTC"
                }},
                "end": {{
                    "dateTime": "YYYY-MM-DDTHH:MM:SS",
                    "timeZone": "UTC"
                }},
                "location": {{
                    "displayName": "Meeting location if specified"
                }},
                "reminderMinutesBeforeStart": 15
            }}
        ]
    }}

    Requirements:
    1. The summary should be clear and concise, capturing the main points of the email
    2. Only include the "calendar" array if there are specific time-bound events or todos mentioned
    3. All dates and times should be in ISO format (YYYY-MM-DDTHH:MM:SS)
    4. If no calendar events are found, return only the summary
    5. For calendar events, always include subject, body, start, and end times
    6. Default timeZone to UTC if not specified
    7. Include location only if mentioned in the email

    IMPORTANT:
    - If the client uses time references like "tomorrow", "day after tomorrow", "yesterday", or "day before yesterday", use present date to calculate the reference date.

    Example response if calendar event exists:
    {{
        "summary": "Team meeting discussion about Q4 planning",
        "calendar": [
            {{
                "subject": "Q4 Planning Meeting",
                "body": {{
                    "contentType": "HTML",
                    "content": "Team meeting for Q4 planning discussion"
                }},
                "start": {{
                    "dateTime": "2024-03-20T14:00:00",
                    "timeZone": "UTC"
                }},
                "end": {{
                    "dateTime": "2024-03-20T15:00:00",
                    "timeZone": "UTC"
                }},
                "location": {{
                    "displayName": "Conference Room"
                }},
                "reminderMinutesBeforeStart": 15
            }}
        ]
    }}

    Example response if no calendar event:
    {{
        "summary": "Update on project status with current progress details"
    }}

    Analyze the email and provide the appropriate JSON response:
    """
    return prompt