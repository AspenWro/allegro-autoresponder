import requests
import os
from github import Github

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

GH_PAT = os.environ["GH_PAT"]
GH_REPO = os.environ["GH_REPO"]

PROCESSED_FILE = "processed_messages.txt"


def get_access_token():
    url = "https://allegro.pl/auth/oauth/token"

    response = requests.post(
        url,
        headers={
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN
        },
        auth=(CLIENT_ID, CLIENT_SECRET)
    )

    token_data = response.json()

    if "access_token" not in token_data:
        print("❌ Błąd tokena:", token_data)
        raise Exception("Nie udało się pobrać access_token")

    print("✅ Access token OK")

    try:
        new_refresh_token = token_data["refresh_token"]
        update_github_secret(new_refresh_token)
    except Exception as e:
        print("⚠️ Nie udało się odświeżyć refresh tokena:", e)

    return token_data["access_token"]


def update_github_secret(new_token):
    try:
        g = Github(GH_PAT)
        repo = g.get_repo(GH_REPO)

        print("🔄 Aktualizacja refresh tokena...")

        repo.create_secret(
            "REFRESH_TOKEN",
            new_token
        )

        print("✅ Refresh token zaktualizowany")

    except Exception as e:
        print("⚠️ Błąd aktualizacji refresh tokena:", e)


def load_processed_messages():
    if not os.path.exists(PROCESSED_FILE):
        return set()

    with open(PROCESSED_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())


def save_processed_message(message_id):
    with open(PROCESSED_FILE, "a") as f:
        f.write(message_id + "\n")


def push_processed_file():
    try:
        g = Github(GH_PAT)
        repo = g.get_repo(GH_REPO)

        with open(PROCESSED_FILE, "r") as f:
            content = f.read()

        try:
            contents = repo.get_contents(PROCESSED_FILE)

            repo.update_file(
                PROCESSED_FILE,
                "Aktualizacja processed messages",
                content,
                contents.sha
            )

        except Exception:
            repo.create_file(
                PROCESSED_FILE,
                "Dodanie processed messages",
                content
            )

        print("✅ processed_messages.txt zapisany do GitHub")

    except Exception as e:
        print("⚠️ Błąd zapisu processed_messages:", e)


access_token = get_access_token()

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/vnd.allegro.public.v1+json"
}

response = requests.get(
    "https://api.allegro.pl/messaging/threads",
    headers=headers
)

threads = response.json()

if "threads" not in threads:
    print("❌ Błąd pobierania rozmów:")
    print(threads)
    raise Exception("Brak pola threads w odpowiedzi API")

processed_messages = load_processed_messages()

print(f"📨 Pobrano rozmowy: {len(threads['threads'])}")

for thread in threads["threads"]:

    thread_id = thread["id"]

    messages_response = requests.get(
        f"https://api.allegro.pl/messaging/threads/{thread_id}/messages",
        headers=headers
    )

    messages = messages_response.json()

    if "messages" not in messages:
        print(f"⚠️ Brak wiadomości dla wątku {thread_id}")
        continue

    if not messages["messages"]:
        continue

    latest_message = messages["messages"][0]

    message_id = latest_message["id"]

    if message_id in processed_messages:
        print(f"⏭️ Wiadomość już obsłużona: {message_id}")
        continue

    is_interlocutor = latest_message["author"]["isInterlocutor"]

    if not is_interlocutor:
        print(f"⏭️ Własna wiadomość: {message_id}")
        save_processed_message(message_id)
        continue

    text = latest_message.get("text", "")

    print("\n--------------------")
    print("🧵 ID:", thread_id)
    print("📩 Message ID:", message_id)
    print("👤 Login:", thread["interlocutor"]["login"])
    print("💬:", text[:300])

    if (
        "zamówienie" in text.lower()
        or "dziękujemy za złożenie zamówienia" in text.lower()
        or "wiadomość generowana automatycznie" in text.lower()
    ):
        print("⛔ Pominięto (system / zamówienie)")
        save_processed_message(message_id)
        continue

    print("✅ NOWA WIADOMOŚĆ OD KLIENTA")

    if "#TEST" not in text:
        print("🛡️ Tryb testowy - brak znacznika #TEST")
        save_processed_message(message_id)
        continue

    print("🧪 Wykryto wiadomość testową")

    reply_url = f"https://api.allegro.pl/messaging/threads/{thread_id}/messages"

    reply_response = requests.post(
        reply_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.allegro.public.v1+json",
            "Content-Type": "application/vnd.allegro.public.v1+json"
        },
        json={
            "text": "To jest odpowiedź testowa autorespondera Aspen.",
            "attachments": []
        }
    )

    print("📤 Status odpowiedzi:", reply_response.status_code)
    print(reply_response.text)

    save_processed_message(message_id)

push_processed_file()
