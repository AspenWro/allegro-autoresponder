import os
import requests
from requests.auth import HTTPBasicAuth

# =========================
# 🔐 SECRETS
# =========================
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

# =========================
# 🧠 TOKEN (SAFE HANDLING)
# =========================
def get_access_token():
    response = requests.post(
        "https://allegro.pl/auth/oauth/token",
        auth=HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET),
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN
        }
    )

    data = response.json()

    if "access_token" not in data:
        print("❌ Błąd tokena:", data)
        raise Exception("Nie udało się pobrać access_token")

    return data["access_token"]

access_token = get_access_token()
print("✅ Access token OK")

# =========================
# 🌐 HEADERS
# =========================
headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/vnd.allegro.public.v1+json"
}

# =========================
# 📬 POBRANIE ROZMÓW
# =========================
threads_response = requests.get(
    "https://api.allegro.pl/messaging/threads",
    headers=headers
)

threads_data = threads_response.json()
threads = threads_data.get("threads", [])

print("📨 Pobrano rozmowy:", len(threads))

# =========================
# 🧠 FILTRY WIADOMOŚCI
# =========================
def is_system_message(text: str) -> bool:
    if not text:
        return True

    blockers = [
        "wiadomość generowana automatycznie",
        "dziękujemy za złożenie zamówienia",
        "zamówienie dotyczy",
        "prosimy nie odpowiadać",
        "baseLinker",
    ]

    lower = text.lower()
    return any(b.lower() in lower for b in blockers)

# =========================
# 💬 ODPOWIEDŹ
# =========================
def send_reply(thread_id):
    url = f"https://api.allegro.pl/messaging/threads/{thread_id}/messages"

    payload = {
        "text": "Dziękujemy za wiadomość 👍 Odpowiemy najszybciej jak to możliwe."
    }

    r = requests.post(url, headers=headers, json=payload)

    print("📤 Odpowiedź status:", r.status_code)

# =========================
# 🔁 GŁÓWNA PĘTLA
# =========================
for thread in threads[:10]:

    thread_id = thread.get("id")

    messages_response = requests.get(
        f"https://api.allegro.pl/messaging/threads/{thread_id}/messages",
        headers=headers
    )

    messages_data = messages_response.json()
    messages = messages_data.get("messages", [])

    if not messages:
        continue

    last_message = messages[-1]
    text = last_message.get("text", "")
    author = last_message.get("author", {}).get("login", "")

    print("\n--------------------")
    print("🧵 ID:", thread_id)
    print("👤 Autor:", author)
    print("💬:", text)

    # 🧯 FILTR SYSTEMOWYCH WIADOMOŚCI
    if is_system_message(text):
        print("⛔ Pominięto (system / zamówienie)")
        continue

    # 🧠 PROSTA OCHRONA (na start)
    if author == "self":
        print("⛔ Pominięto (własna wiadomość)")
        continue

    # 📬 ODPOWIEDŹ
    send_reply(thread_id)
