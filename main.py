import os
import requests
from requests.auth import HTTPBasicAuth

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

# Pobranie nowego access tokena
response = requests.post(
    "https://allegro.pl/auth/oauth/token",
    auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
    data={
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }
)

token_data = response.json()

access_token = token_data["access_token"]

print("Pobrano access token")

# Nagłówki do API Allegro
headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/vnd.allegro.public.v1+json"
}

# Pobranie wiadomości
messages_response = requests.get(
    "https://api.allegro.pl/messaging/threads",
    headers=headers
)

print(messages_response.json())
