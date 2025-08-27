import json
import time
from typing import (
    TypedDict,
    Literal
)

from django.conf import settings
from langgraph.graph import StateGraph

from .client import clients
from .prompts import generate_email_summary_and_events


class State(TypedDict):
    prompt: str
    response: dict
    status: Literal['success', 'error']
    message: str


def call_with_retry(state: State, retries: int = 3, delay: int = 2) -> dict:
    """Call Azure OpenAI, ensure JSON output, retry if invalid."""
    
    prompt = state.get("prompt")
    
    for attempt in range(1, retries + 1):
        try:
            resp = clients.client_azure_openai.chat.completions.create(
                model=settings.AZURE_DEPLOYMENT,
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


def build_graph():
    graph = StateGraph(State)
    graph.add_node("generate", generate_json)
    graph.set_entry_point("generate")
    graph.set_finish_point("generate")
    return graph.compile()


def create_initial_state(prompt: str | None = None):
    return State({
        "prompt": prompt,
    })


def summarize_email_content(email_content: str, subject: str):
    app = build_graph()
    prompt = generate_email_summary_and_events(email_content, subject)
    state = create_initial_state(prompt=prompt)
    final_state = app.invoke(state)
    return final_state.get("response")
