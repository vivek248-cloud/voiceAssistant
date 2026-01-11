import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load .env file
load_dotenv()

# Read API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in .env file")

# Create OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

ASSISTANT_NAME = "Asifa"


def ai_chat(text: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are Asifa, a polite female voice assistant."
            },
            {
                "role": "user",
                "content": text
            }
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

    if "play" in cmd and "youtube" in cmd:
        song = cmd.replace("play", "").replace("on youtube", "").strip()
        return {
            "action": "open",
            "url": f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}",
            "text": f"Playing {song} on YouTube"
        }

    if "play" in cmd and "spotify" in cmd:
        song = cmd.replace("play", "").replace("on spotify", "").strip()
        return {
            "action": "open",
            "url": f"https://open.spotify.com/search/{song.replace(' ', '%20')}",
            "text": f"Playing {song} on Spotify"
        }

    if "search" in cmd:
        query = cmd.replace("search", "").strip()
        return {
            "action": "open",
            "url": f"https://www.google.com/search?q={query.replace(' ', '+')}",
            "text": f"Searching Google for {query}"
        }

    # Default → AI conversation
    return {
        "action": "speak",
        "text": ai_chat(command)
    }





# from datetime import datetime
# from openai import OpenAI
# import os

# ASSISTANT_NAME = "Jarvis"

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def ai_chat(text):
#     res = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": "You are Jarvis, a polite female voice assistant."},
#             {"role": "user", "content": text}
#         ]
#     )
#     return res.choices[0].message.content

# def process_command(command: str):
#     cmd = command.lower()

#     if "time" in cmd:
#         return {"action": "speak", "text": f"The time is {datetime.now().strftime('%H:%M')}"}

#     if "date" in cmd:
#         return {"action": "speak", "text": f"Today is {datetime.now().strftime('%d %B %Y')}"}

#     if "play" in cmd and "youtube" in cmd:
#         song = cmd.replace("play", "").replace("on youtube", "").strip()
#         return {
#             "action": "open",
#             "url": f"https://www.youtube.com/results?search_query={song.replace(' ', '+')}",
#             "text": f"Playing {song} on YouTube"
#         }

#     if "play" in cmd and "spotify" in cmd:
#         song = cmd.replace("play", "").replace("on spotify", "").strip()
#         return {
#             "action": "open",
#             "url": f"https://open.spotify.com/search/{song.replace(' ', '%20')}",
#             "text": f"Playing {song} on Spotify"
#         }

#     if "search" in cmd:
#         query = cmd.replace("search", "").strip()
#         return {
#             "action": "open",
#             "url": f"https://www.google.com/search?q={query.replace(' ', '+')}",
#             "text": f"Searching Google for {query}"
#         }

#     # fallback → AI conversation
#     return {"action": "speak", "text": ai_chat(command)}
