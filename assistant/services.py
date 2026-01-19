import os
from datetime import datetime
from openai import OpenAI

ASSISTANT_NAME = "Jarvis"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)


def ai_chat(text: str) -> str:
    if not client:
        return "AI service is not configured. Please set the OpenAI API key."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Jarvis, a polite female voice assistant."},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content


def process_command(command: str):
    cmd = command.lower()

    if "time" in cmd:
        return {
            "action": "speak",
            "text": f"The time is {datetime.now().strftime('%H:%M')}"
        }

    if "date" in cmd:
        return {
            "action": "speak",
            "text": f"Today is {datetime.now().strftime('%d %B %Y')}"
        }

    return {
        "action": "speak",
        "text": ai_chat(command)
    }
