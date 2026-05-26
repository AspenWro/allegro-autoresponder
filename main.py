import os
import requests
from requests.auth import HTTPBasicAuth

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

# Pobranie access tokena
response = requests.post(
    "https://allegro.pl/auth/oauth/token",
    auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
    data={
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }
)

token_data = response.json()

print(token_data)

access_token = token_data["access_token"]

print("Access token OK")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/vnd.allegro.public.v1+json"
}

# Pobranie listy rozmów
threads_response = requests.get(
    "https://api.allegro.pl/messaging/threads",
    headers=headers
)

threads_data = threads_response.json()

print("Pobrano rozmowy")

# Wyświetlenie rozmów i ostatnich wiadomości
for thread in threads_data.get("threads", [])[:5]:

    thread_id = thread.get("id")

    print("------------------")
    print("ID rozmowy:", thread_id)

    messages_response = requests.get(
        f"https://api.allegro.pl/messaging/threads/{thread_id}/messages",
        headers=headers
    )

    messages_data = messages_response.json()

    messages = messages_data.get("messages", [])

    if messages:

        last_message = messages[-1]

        text = last_message.get("text")
        author = last_message.get("author", {}).get("login")

        print("Autor:", author)
        print("Treść:", text)

    else:
        print("Brak wiadomości")
