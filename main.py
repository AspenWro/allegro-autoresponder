import os
import requests
from requests.auth import HTTPBasicAuth

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

GH_PAT = os.environ["GH_PAT"]
REPO_NAME = os.environ["REPO_NAME"]
GITHUB_USERNAME = os.environ["ASPENWRO_NAME"]

# Pobranie nowych tokenów
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
new_refresh_token = token_data["refresh_token"]

print("Nowy access token OK")

# Aktualizacja GitHub Secret
github_response = requests.put(
    f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/actions/secrets/REFRESH_TOKEN",
    headers={
        "Authorization": f"Bearer {GH_PAT}",
        "Accept": "application/vnd.github+json"
    },
    json={
        "encrypted_value": new_refresh_token,
        "key_id": "temporary"
    }
)

print("Próba aktualizacji refresh token")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/vnd.allegro.public.v1+json"
}

threads_response = requests.get(
    "https://api.allegro.pl/messaging/threads",
    headers=headers
)

threads_data = threads_response.json()

print("Pobrano rozmowy")

for thread in threads_data.get("threads", [])[:3]:

    print("----------------")
    print(thread.get("id"))
