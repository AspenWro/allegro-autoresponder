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
# 🧠 STATE (PAMIĘĆ BOTA)
# =========================
STATE_FILE = "processed_threads.txt"

def load_processed():
    if not os.path.exists(STATE_FILE):
        return set()

    with open(STATE_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())


def save_processed(processed):
    with open(STATE_FILE, "w") as f:
        for item in processed:
            f.write(item + "\n")

processed_threads = load_processed()

# =========================
# 🔑 TOKEN
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
# 📨 ROZMOWY
# =========================
threads_response = requests.get(
    "https://api.allegro.pl/messaging/threads",
    headers=headers
)

threads_data = threads_response.json()
threads = threads_data.get("threads", [])

print(f"📨 Pobrano rozmowy: {len(threads)}")

# =========================
# 🧯 FILTR SYSTEMOWYCH
# =========================
def is_system_message(text: str) -> bool:
    if not text:
        return True

    blockers = [
        "wiadomość generowana automatycznie",
        "dziękujemy za złożenie zamówienia",
        "zamówienie dotyczy",
        "prosimy nie odpowiadać",
        "baselinker",
    ]

    lower = text.lower()
    return any(b.lower() in lower for b in blockers)

# =========================
# 📬 ODPOWIEDŹ
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

    # 🧠 ANTI-DUPLICATE
    if thread_id in processed_threads:
        print("⏭️ Już obsłużone:", thread_id)
        continue

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

    # 🧯 SYSTEM FILTER
    if is_system_message(text):
        print("⛔ Pominięto (system / zamówienie)")
        processed_threads.add(thread_id)
        continue

    # 🧠 SELF CHECK
    if author == "self":
        print("⛔ Pominięto (własna wiadomość)")
        processed_threads.add(thread_id)
        continue

    # 📬 ODPOWIEDŹ
    send_reply(thread_id)

    # 💾 ZAPIS DO PAMIĘCI
    processed_threads.add(thread_id)

# 💾 ZAPIS STANU
save_processed(processed_threads) 
