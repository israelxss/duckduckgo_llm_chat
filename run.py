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
import re

def reverse_hebrew_words(text):
    def reverse_if_hebrew(word):
        return word[::-1] if re.search(r'[\u0590-\u05FF]', word) else word

    words = re.split(r'(\s+)', text) 
    processed_words = [reverse_if_hebrew(word) for word in words] 
    reversed_text = ''.join(processed_words).split()
    return ' '.join(reversed(reversed_text))


# Constants
CHAT_URL = "https://duckduckgo.com/duckchat/v1/chat"
STATUS_URL = "https://duckduckgo.com/duckchat/v1/status"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "text/event-stream"
}

# AI models dictionary
AI_MODELS = {
    "1": "gpt-4o-mini",
    "2": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "3": "claude-3-haiku-20240307",
    "4": "o3-mini",
    "5": "mistralai/Mistral-Small-24B-Instruct-2501"
}


def choose_model():
    """Prompt the user to choose an AI model."""
    print("\nPlease choose an AI model:")
    print("1. GPT-4o mini")
    print("2. Llama 3.1 70B (open source)")
    print("3. Claude 3 Haiku")
    print("4. o3-mini (beta)")
    print("5. Mistral Small 3 (open source)")

    while True:
        choice = input("Enter your choice (1-5): ").strip()
        if choice in AI_MODELS:
            return AI_MODELS[choice]
        else:
            print("Invalid choice. Please try again.")


def fetch_vqd():
    """Fetch the VQD from DuckDuckGo."""
    headers = {"x-vqd-accept": "1"}
    response = requests.get(STATUS_URL, headers=headers)
    if response.status_code == 200:
        return response.headers.get("x-vqd-4")
    else:
        raise Exception(f"Failed to initialize chat: {response.status_code} {response.text}")


def fetch_response(vqd, model, messages):
    """Send the message to the chat and return the response."""
    payload = {
        "model": model,
        "messages": messages
    }

    headers = {**HEADERS, "x-vqd-4": vqd}

    response = requests.post(CHAT_URL, headers=headers, json=payload, stream=True)
    if response.status_code != 200:
        raise Exception(f"Failed to send message: {response.status_code} {response.text}")

    return response


def process_stream(response, output_queue):
    """Process the stream of messages from the AI."""
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


def chat_loop(vqd, model):
    """Main loop to handle user input and AI responses."""
    messages = []

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except KeyboardInterrupt:
            print("\nExiting chat. Goodbye!")
            break

        if user_input.lower() == "exit":
            print("Exiting chat. Goodbye!")
            break

        messages.append({"content": user_input, "role": "user"})

        try:
            response = fetch_response(vqd, model, messages)
        except Exception as e:
            print(f"Error: {e}")
            continue

        output_queue = Queue()
        thread = Thread(target=process_stream, args=(response, output_queue))
        thread.start()

        print("\nAI:", end=" ")
        #while thread.is_alive() or not output_queue.empty():
            #while not output_queue.empty():
                #print(output_queue.get(), end="", flush=True)
        output_text = ""
        while thread.is_alive() or not output_queue.empty():
            while not output_queue.empty():
                output_text += output_queue.get()
        print(reverse_hebrew_words(output_text))

        print()
        thread.join()


def main():
    """Main function to initialize the chat and handle the conversation."""
    print("Welcome to DuckDuckGo AI Chat CLI!")

    # Choose AI model
    model = choose_model()

    # Fetch VQD
    try:
        vqd = fetch_vqd()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print("\nChat initialized successfully. You can start chatting now.")
    print("Type 'exit' to end the conversation.\n")

    # Start chat loop
    chat_loop(vqd, model)


if __name__ == "__main__":
    main()
