def generate_email_summary_and_events(email_content, subject):
    """
    Generates a prompt for email summarization, calendar event detection, 
    and drafting a general reply email in full HTML format.
    Returns a structured prompt that can be sent to an LLM.
    """
    prompt = f"""
    Analyze the following email and:
    1. Provide a clear and concise summary
    2. Extract any calendar events or todos (if they exist)
    3. Generate a general, polite, and professional reply as a complete HTML document string.
       - The reply should acknowledge the email without assuming specific actions (accept/decline/etc.)
       - Include <!DOCTYPE html>, <html>, <head>, and <body>
       - Use semantic HTML elements (<p>, <strong>, <em>, <mark>, <ul>, <blockquote>, <table>, etc.)
       - Add minimal inline CSS for readability
       - Include greeting and sign-off
       - Keep it neutral, appreciative, and adaptable for any context

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
        ],
        "reply": "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><title>Email Reply</title><style>body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }} p {{ margin-bottom: 12px; }} mark {{ background-color: #fffd75; }}</style></head><body><p>Hello <strong>[Recipient’s Name]</strong>,</p><p>Thank you for your email. I appreciate you taking the time to reach out and share these details.</p><p>I’ll carefully review the information provided and get back to you if further clarification is needed. In the meantime, please don’t hesitate to send any additional updates.</p><blockquote><em>Your message has been noted and is valued.</em></blockquote><p>Best regards,<br>[Your Name]</p></body></html>"
    }}

    Requirements:
    1. The summary should be clear and concise, capturing the main points of the email
    2. Only include the "calendar" array if there are specific time-bound events or todos mentioned
    3. All dates and times should be in ISO format (YYYY-MM-DDTHH:MM:SS)
    4. If no calendar events are found, return only summary and reply
    5. For calendar events, always include subject, body, start, and end times
    6. Default timeZone to UTC if not specified
    7. Include location only if mentioned in the email
    8. The "reply" must always be included, even if no events are found
    9. The reply must be a valid HTML document string (escaped inside JSON)

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
        ],
        "reply": "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><title>Email Reply</title><style>body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }} p {{ margin-bottom: 12px; }} mark {{ background-color: #fffd75; }}</style></head><body><p>Hello <strong>Team</strong>,</p><p>Thank you for your email regarding the upcoming meeting. I’ve noted the details and will review the agenda ahead of time.</p><p>Looking forward to the discussion.</p><p>Best regards,<br>Alex</p></body></html>"
    }}

    Example response if no calendar event:
    {{
        "summary": "Update on project status with current progress details",
        "reply": "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><title>Email Reply</title><style>body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }} p {{ margin-bottom: 12px; }} mark {{ background-color: #fffd75; }}</style></head><body><p>Hello <strong>[Recipient’s Name]</strong>,</p><p>Thank you for your update. I appreciate the information and will review it carefully.</p><p>Please feel free to share any further details whenever convenient.</p><p>Best regards,<br>[Your Name]</p></body></html>"
    }}

    Analyze the email and provide the appropriate JSON response:
    """
    return prompt
