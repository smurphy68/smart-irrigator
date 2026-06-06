import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def notify(message):
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": f"🍓 Pi: {message}"})


notify("Service started")

while True:
    print("Hello, World!")
    time.sleep(5)