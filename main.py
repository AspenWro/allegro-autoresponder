import os
import requests
from requests.auth import HTTPBasicAuth

# === SECRETS Z GITHUB ===
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

# === 1. POBRANIE ACCESS TOKENA ===
token_response = requests.post(
    "https://allegro.pl/auth/oauth/token",
    auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
    data={
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }
)

token_data = token_response.json()
print(token_data)

if "access_token" not in token_data:
    raise Exception("Brak access_token - sprawdź refresh token")

access_token = token_data["access_token"]

print("Access token OK")

# === HEADERS DO API ===
headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/vnd.allegro.public.v1+json"
}

# === 2. POBRANIE ROZMÓW ===
threads_response = requests.get(
    "https://api.allegro.pl/messaging/threads",
    headers=headers
)

threads_data = threads_response.json()

print("Pobrano rozmowy")

threads = threads_data.get("threads", [])

# === 3. WYŚWIETLENIE WIADOMOŚCI ===
for thread in threads[:5]:

    thread_id = thread.get("id")

    print("\n--------------------")
    print("ID rozmowy:", thread_id)

    messages_response = requests.get(
        f"https://api.allegro.pl/messaging/threads/{thread_id}/messages",
        headers=headers
    )

    messages_data = messages_response.json()
    messages = messages_data.get("messages", [])

    if not messages:
        print("Brak wiadomości")
        continue

    last_message = messages[-1]

    author = last_message.get("author", {}).get("login")
    text = last_message.get("text")

    print("Autor:", author)
    print("Treść:", text)
