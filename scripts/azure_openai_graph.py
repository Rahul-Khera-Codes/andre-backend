import os
import json
import time
from typing import (
    TypedDict,
    Literal
)

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from openai import AzureOpenAI
from pydantic import BaseModel

assert load_dotenv()


# ---- 1. Define State ----
class State(TypedDict):
    prompt: str
    response: dict
    status: Literal['success', 'error']
    message: str


# ---- 2. Azure OpenAI Client ----

client = AzureOpenAI(
    api_version=os.getenv("AZURE_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_API_KEY"),
)



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


# ---- 3. Helper function with retry ----
def call_with_retry(state: State, retries: int = 3, delay: int = 2) -> dict:
    """Call Azure OpenAI, ensure JSON output, retry if invalid."""
    
    prompt = state.get("prompt")
    
    for attempt in range(1, retries + 1):
        try:
            resp = client.chat.completions.create(
                model=os.getenv("AZURE_DEPLOYMENT"),  # your deployment name
                messages=[
                    {"role": "system", "content": "You are a JSON-only API. Always return valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )

            content = resp.choices[0].message.content.strip()
            content = content.replace("```json", "").replace("```", "")

            # Try parsing as JSON
            state['response'] = json.loads(content)
            state['status'] = "success"
            state['message'] = 'Summarized successfully.'
            
            return state

        except (json.JSONDecodeError, KeyError) as e:
            if attempt < retries:
                time.sleep(delay * attempt)  # exponential backoff
                continue

            state['status'] = "error"
            state['message'] = f'Error while summarizing: {e}'
            return state


def generate_json(state: State):
    state = call_with_retry(state)
    return state


graph = StateGraph(State)
graph.add_node("generate", generate_json)
graph.set_entry_point("generate")
graph.set_finish_point("generate")

app = graph.compile()


def create_initial_state(prompt: str | None = None):
    return State({
        "prompt": prompt,
    })

# ---- 6. Run Example ----
if __name__ == "__main__":
    email_content = "Ok, we'll have a meeting at 12pm on 22-08-2025, and after that we will have the client meet at 3pm on 23-08-2025"
    subject = ""
    prompt = generate_email_summary_and_events(email_content, subject)
    state = create_initial_state(prompt=prompt)
    final_state = app.invoke(state)
    final_response = final_state.get("response")
    print("Final JSON:", json.dumps(final_response, indent=4))
