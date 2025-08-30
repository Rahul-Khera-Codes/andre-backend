#!/usr/bin/env python3
"""
Single-file demo: Azure OpenAI Responses API + Vector Store (no DB)

Usage:
  python document_summarization.py --client-id client_123 \
      --files ./docs/contract.pdf ./docs/budget.xlsx \
      --question "Does the contract allow early delivery and is it within budget?"
"""

import datetime
import os
import sys
import argparse
from typing import (
    Any,
    Dict,
    List, 
)
import uuid


from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

AZURE_OPENAI_KEY = os.environ.get("AZURE_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = "2025-03-01-preview"
MODEL = os.environ.get("AZURE_MODEL_NAME", "gpt-4o-mini")


# In-memory session store (replace with DB for production)
SESSION_HISTORY: Dict[str, List[Dict[str, Any]]] = {}

def require_env():
    missing = []
    if not AZURE_OPENAI_KEY: missing.append("AZURE_API_KEY")
    if not AZURE_OPENAI_ENDPOINT: missing.append("AZURE_ENDPOINT")
    if not AZURE_OPENAI_API_VERSION: missing.append("AZURE_API_VERSION")
    if missing:
        raise SystemExit(f"Missing env vars: {', '.join(missing)}")

def make_client() -> AzureOpenAI:
    return AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
        api_version=AZURE_OPENAI_API_VERSION,
    )

def create_vector_store_for_client(client, client_id: str):
    return client.vector_stores.create(name=f"kb_{client_id}")

def upload_files_to_vector_store(client, vector_store_id: str, file_paths: List[str]):
    if not file_paths:
        return
    files = [open(p, "rb") for p in file_paths]
    try:
        client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store_id,
            files=files
        )
    finally:
        for f in files:
            f.close()

def add_to_history(session_id: str, role: str, content: str):
    if session_id not in SESSION_HISTORY:
        SESSION_HISTORY[session_id] = []
    SESSION_HISTORY[session_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })

def get_history(session_id: str):
    # Only return role/content for model input
    return [
        {"role": msg["role"], "content": msg["content"]}
        for msg in SESSION_HISTORY.get(session_id, [])
    ]

def ask_question_with_vector_search(client, model: str, vector_store_id: str, session_id: str, question: str):
    # Build conversation history for context
    history = get_history(session_id)
    # Add the new user question
    history_plus_question = history + [{"role": "user", "content": question}]
    response = client.responses.create(
        model=model,
        input=history_plus_question,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vector_store_id]
        }],
        stream=False,
    )
    # Save user question and assistant response
    add_to_history(session_id, "user", question)
    if response.output_text:
        add_to_history(session_id, "assistant", response.output_text)
    return response



def interactive_chat(client, vector_store_id: str, session_id: str):
    """Run interactive chat session"""
    print("\n=== Document Q&A Chatbot ===")
    print("Type 'exit' or press Ctrl+C to end the conversation\n")
    
    while True:
        try:
            # Get user input
            question = input("\nYou: ").strip()
            
            # Check for exit command
            if question.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break
            
            if not question:
                continue
                
            # Get response
            print("\nAssistant: ", end='', flush=True)
            response = ask_question_with_vector_search(
                client, 
                MODEL, 
                vector_store_id, 
                session_id, 
                question
            )
            
            # Print response
            if response.output_text:
                print(response.output_text)
            else:
                print("(No response generated)")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Azure OpenAI Responses API + Vector Store demo (no DB)")
    parser.add_argument("--client-id", required=True, help="Logical client/tenant id")
    parser.add_argument("--files", nargs="*", default=[], help="Paths to files to upload into the client's KB")
    # parser.add_argument("--question", required=True, help="User question to ask")
    parser.add_argument("--session-id", default=None, help="Session ID to continue a conversation")
    args = parser.parse_args()

    require_env()
    client = make_client()

    # 1) Create per-client vector store
    # print(f"[1/4] Creating vector store for client={args.client_id} ...")
    # vector_store = create_vector_store_for_client(client, args.client_id)
    # print(f"     vector_store_id = {vector_store.id}")
    vector_store_id = "vs_vMcM68NtMy4q88AVy5DYHtkg"


    # Upload files if provided
    if args.files:
        print(f"\nUploading {len(args.files)} file(s) to knowledge base...")
        upload_files_to_vector_store(client, vector_store_id, args.files)
        print("Upload complete!\n")

    # Start chat session
    session_id = args.session_id or str(uuid.uuid4())
    interactive_chat(client, vector_store_id, session_id)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)