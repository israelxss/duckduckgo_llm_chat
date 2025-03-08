"""
This script is based on the original code from the following source:
https://gist.github.com/sukhbinder/a0af1b6649116a0c3787d5eec882eaa4

The original script had some issues that didn't work as expected,  
so I made modifications to fix and improve it.
"""

import requests
import json
import sys
from threading import Thread
from queue import Queue

def choose_model():
    print()
    print("Please choose an AI model:")
    print("1. GPT-4o mini")
    print("2. Llama 3.1 70B (open source)")
    print("3. Claude 3 Haiku")
    print("4. o3-mini (beta)")
    print("5. Mistral Small 3 (open source)")
    print()

    models = {
        "1": "gpt-4o-mini",
        "2": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "3": "claude-3-haiku-20240307",
        "4": "o3-mini",
        "5": "mistralai/Mistral-Small-24B-Instruct-2501"
    }

    while True:
        choice = input("Enter your choice (1-5): ").strip()
        if choice in models:
            return models[choice]
        else:
            print("Invalid choice. Please try again.")

def fetch_vqd():
    url = "https://duckduckgo.com/duckchat/v1/status"
    headers = {"x-vqd-accept": "1"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.headers.get("x-vqd-4")
    else:
        raise Exception(f"Failed to initialize chat: {response.status_code} {response.text}")

def fetch_response(chat_url, vqd, model, messages):
    payload = {
        "model": model,
        "messages": messages
    }
    headers = {
        "x-vqd-4": vqd,
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }
    response = requests.post(chat_url, headers=headers, json=payload, stream=True)
    if response.status_code != 200:
        raise Exception(f"Failed to send message: {response.status_code} {response.text}")
    return response

def process_stream(response, output_queue):
    for line in response.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line == "data: [DONE]":
                break
            if line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    message = data.get("message", "")
                    if message:
                        output_queue.put(message)
                except json.JSONDecodeError:
                    continue

def main():
    """Inspired by duckduckGO-chat-cli"""

    print("Welcome to DuckDuckGo AI Chat CLI!")

    model = choose_model()

    try:
        vqd = fetch_vqd()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print()
    print("Chat initialized successfully. You can start chatting now.")
    print("Type 'exit' to end the conversation.")
    print()

    chat_url = "https://duckduckgo.com/duckchat/v1/chat"
    messages = []

    while True:
        print()
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("Exiting chat. Goodbye!")
            break

        messages.append({"content": user_input, "role": "user"})

        try:
            response = fetch_response(chat_url, vqd, model, messages)
        except Exception as e:
            print(f"Error: {e}")
            continue

        output_queue = Queue()
        thread = Thread(target=process_stream, args=(response, output_queue))
        thread.start()

        print()
        print("AI:", end=" ")
        while thread.is_alive() or not output_queue.empty():
            while not output_queue.empty():
                print(output_queue.get(), end="", flush=True)

        print()
        thread.join()

if __name__ == "__main__":
    main()
