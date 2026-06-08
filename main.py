import requests
import os
import json
from github import Github

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

GH_PAT = os.environ["GH_PAT"]
GH_REPO = os.environ["GH_REPO"]

PROCESSED_FILE = "processed_threads.txt"


def get_access_token():
    url = "https://allegro.pl/auth/oauth/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    }

    response = requests.post(
        url,
        headers=headers,
        data=data,
        auth=(CLIENT_ID, CLIENT_SECRET)
    )

    token_data = response.json()

    if "access_token" not in token_data:
        print("❌ Błąd tokena:", token_data)
        raise Exception("Nie udało się pobrać access_token")

    print("✅ Access token OK")

    new_refresh_token = token_data["refresh_token"]
    update_github_secret(new_refresh_token)

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
        print("⚠️ Nie udało się zaktualizować tokena:", e)


def load_processed_threads():
    if not os.path.exists(PROCESSED_FILE):
        return set()

    with open(PROCESSED_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())


def save_processed_thread(thread_id):
    with open(PROCESSED_FILE, "a") as f:
        f.write(thread_id + "\n")


def push_processed_file():
    try:
        g = Github(GH_PAT)
        repo = g.get_repo(GH_REPO)

        with open(PROCESSED_FILE, "r") as f:
            content = f.read()

        path = PROCESSED_FILE

        try:
            contents = repo.get_contents(path)

            repo.update_file(
                path,
                "Aktualizacja processed threads",
                content,
                contents.sha
            )

        except:
            repo.create_file(
                path,
                "Dodanie processed threads",
                content
            )

        print("✅ processed_threads.txt zapisany do GitHub")

    except Exception as e:
        print("⚠️ Błąd zapisu processed_threads:", e)


access_token = get_access_token()
me = requests.get(
    "https://api.allegro.pl/me",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.allegro.public.v1+json"
    }
)

print("=== KONTO ALLEGRO ===")
print(me.text)
print("=====================")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/vnd.allegro.public.v1+json"
}

response = requests.get(
    "https://api.allegro.pl/messaging/threads",
    headers=headers
)
print("=== THREADS API RESPONSE ===")
print(response.text)
print("=== KONIEC RESPONSE ===")

threads = response.json()

processed_threads = load_processed_threads()

print(f"📨 Pobrano rozmowy: {len(threads['threads'])}")

for thread in threads["threads"]:
    print("THREAD:", thread["id"])

for thread in threads["threads"]:

    thread_id = thread["id"]

    if thread_id in processed_threads:
        print(f"⏭️ Już obsłużone: {thread_id}")
        

    messages_response = requests.get(
        f"https://api.allegro.pl/messaging/threads/{thread_id}/messages",
        headers=headers
    )

    messages = messages_response.json()
    print("LICZBA WIADOMOŚCI:", len(messages.get("messages", [])))

    if not messages["messages"]:
        continue

    last_message = messages["messages"][-1]
    print("=== LAST MESSAGE ===")
    print(json.dumps(last_message, indent=2, ensure_ascii=False))
    print("====================")
    print("NADAWCA:", last_message.get("author", {}))

    for msg in messages["messages"]:
    print("\n=== MESSAGE ===")
    print(json.dumps(msg, indent=2, ensure_ascii=False))
    print("===============\n")

    text = last_message.get("text", "")

    print("\n--------------------")
    print("🧵 ID:", thread_id)
    print("👤 Login:", thread["interlocutor"]["login"])
    print("💬:", text[:300])

    if (
        "zamówienie" in text.lower()
        or "dziękujemy za złożenie zamówienia" in text.lower()
        or "wiadomość generowana automatycznie" in text.lower()
    ):
        print("⛔ Pominięto (system / zamówienie)")
        save_processed_thread(thread_id)
        continue

    print("✅ NOWA WIADOMOŚĆ OD KLIENTA")

    if "#TEST" not in text:
        print("🛡️ Tryb testowy - brak znacznika #TEST")
        save_processed_thread(thread_id)
        continue

    print("🧪 Wykryto wiadomość testową")

    reply_url = f"https://api.allegro.pl/messaging/threads/{thread_id}/messages"

    reply_payload = {
        "text": "To jest odpowiedź testowa autorespondera Aspen."
    }

    reply_response = requests.post(
        reply_url,
        headers={
            **headers,
            "Content-Type": "application/json"
        },
        json=reply_payload
    )

    print("📤 Status odpowiedzi:", reply_response.status_code)
    print(reply_response.text)

    save_processed_thread(thread_id)

push_processed_file()
