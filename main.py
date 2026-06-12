import requests
import os
from github import Github
from datetime import datetime

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

GH_PAT = os.environ["GH_PAT"]
GH_REPO = os.environ["GH_REPO"]

ANSWERED_FILE = "answered_threads.txt"

AUTOREPLY_TEXT = """Dziękujemy za wiadomość.

Obecnie kontaktujesz się z nami poza standardowymi godzinami pracy. Otrzymaliśmy Twoją wiadomość i odpowiemy tak szybko, jak to możliwe w najbliższym dniu roboczym.

Pozdrawiamy
Zespół Aspen"""


def is_weekend_mode():
    now = datetime.now()

    weekday = now.weekday()
    hour = now.hour

    if weekday == 4 and hour >= 16:
        return True

    if weekday == 5:
        return True

    if weekday == 6:
        return True

    if weekday == 0 and hour < 8:
        return True

    return False


def get_weekend_key():
    now = datetime.now()
    year, week, _ = now.isocalendar()
    return f"{year}-W{week}"


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


def load_answered_threads():
    if not os.path.exists(ANSWERED_FILE):
        return set()

    with open(ANSWERED_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())


def save_answered_thread(thread_key):
    with open(ANSWERED_FILE, "a") as f:
        f.write(thread_key + "\n")


def push_answered_file():
    try:
        g = Github(GH_PAT)
        repo = g.get_repo(GH_REPO)

        with open(ANSWERED_FILE, "r") as f:
            content = f.read()

        try:
            contents = repo.get_contents(ANSWERED_FILE)

            repo.update_file(
                ANSWERED_FILE,
                "Aktualizacja answered threads",
                content,
                contents.sha
            )

        except Exception:
            repo.create_file(
                ANSWERED_FILE,
                "Dodanie answered threads",
                content
            )

        print("✅ answered_threads.txt zapisany do GitHub")

    except Exception as e:
        print("⚠️ Błąd zapisu answered_threads:", e)


if not is_weekend_mode():
    print("⏭️ Poza godzinami działania autorespondera")
    raise SystemExit(0)

weekend_key = get_weekend_key()

print(f"📅 Weekend key: {weekend_key}")

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

answered_threads = load_answered_threads()

print(f"📨 Pobrano rozmowy: {len(threads['threads'])}")

for thread in threads["threads"]:

    thread_id = thread["id"]

    weekend_thread_key = f"{thread_id}|{weekend_key}"

    if weekend_thread_key in answered_threads:
        print(f"⏭️ Już odpowiedziano w ten weekend: {thread_id}")
        continue

    messages_response = requests.get(
        f"https://api.allegro.pl/messaging/threads/{thread_id}/messages",
        headers=headers
    )

    messages = messages_response.json()

    if "messages" not in messages:
        continue

    if not messages["messages"]:
        continue

    latest_client_message = None

    for message in messages["messages"]:
        author = message.get("author", {})

        if author.get("isInterlocutor") is True:
            latest_client_message = message
            break

    if latest_client_message is None:
        continue

    text = latest_client_message.get("text", "")

    if (
        "zamówienie" in text.lower()
        or "dziękujemy za złożenie zamówienia" in text.lower()
        or "wiadomość generowana automatycznie" in text.lower()
    ):
        continue

    if "#TEST" not in text:
        continue

    print("\n--------------------")
    print("🧵 ID:", thread_id)
    print("👤 Login:", thread["interlocutor"]["login"])
    print("🧪 Wykryto wiadomość testową")
    print("📤 Wysyłam autoresponder weekendowy")

    reply_url = f"https://api.allegro.pl/messaging/threads/{thread_id}/messages"

    reply_response = requests.post(
        reply_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.allegro.public.v1+json",
            "Content-Type": "application/vnd.allegro.public.v1+json"
        },
        json={
            "text": AUTOREPLY_TEXT,
            "attachments": []
        }
    )

    print("📤 Status odpowiedzi:", reply_response.status_code)

    if reply_response.status_code == 201:
        save_answered_thread(weekend_thread_key)
        print("✅ Zapisano odpowiedź weekendową")
    else:
        print(reply_response.text)

push_answered_file()
