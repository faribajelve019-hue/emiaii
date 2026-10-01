import getpass
import json
import os
import re
import sys
import urllib.error
import urllib.request

API_BASE = "https://hazardstudio.ir/api"

CONFIG_DIR = os.path.expanduser("~/.hazardstudio")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


def request_json(path, data):
    url = API_BASE + path

    body = json.dumps(data).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "HazardStudio-CLI/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw)

    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")

        try:
            return error.code, json.loads(raw)
        except Exception:
            return error.code, {
                "ok": False,
                "message": raw or "HTTP error",
            }

    except Exception as error:
        return 0, {
            "ok": False,
            "message": str(error),
        }


def save_config(api_key, username):
    os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)

    data = {
        "username": username,
        "api_key": api_key,
    }

    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    try:
        os.chmod(CONFIG_FILE, 0o600)
    except Exception:
        pass


def load_config():
    if not os.path.isfile(CONFIG_FILE):
        return None

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return None


def login():
    print()
    print("🚀 HazardStudio Login")
    print("━━━━━━━━━━━━━━━━━━━━")
    print()

    username = input(
        "Enter a username for the new account: "
    ).strip()

    if not username:
        print("❌ Username cannot be empty.")
        return

    password = getpass.getpass("Enter password: ")

    if len(password) < 6:
        print("❌ Password must be at least 6 characters.")
        return

    print()
    print("📡 Creating account...")

    status, result = request_json(
        "/auth/register",
        {
            "username": username,
            "password": password,
        },
    )

    if not result.get("ok"):
        print("❌", result.get(
            "message",
            "Registration failed."
        ))
        return

    api_key = result.get("api_key")

    if not api_key:
        print("❌ Server did not return an API key.")
        return

    save_config(api_key, username)

    print()
    print("🔐 API key generated.")
    print("💾 API key saved locally.")
    print()
    print(f"👤 Username: {username}")
    print("✅ Account created successfully!")


def valid_site_name(name):
    return bool(
        re.fullmatch(
            r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?",
            name
        )
    )


def deploy(filename):
    if not os.path.isfile(filename):
        print(f"❌ File not found: {filename}")
        return

    if not filename.lower().endswith(".tl"):
        print("❌ File must have .tl extension.")
        return

    config = load_config()

    if not config or not config.get("api_key"):
        print("❌ You are not logged in.")
        print()
        print("Run:")
        print("  hazardstudio login")
        return

    size = os.path.getsize(filename)

    if size > 2 * 1024 * 1024:
        print("❌ app.tl is larger than 2 MB.")
        return

    try:
        with open(filename, "r", encoding="utf-8") as file:
            html = file.read()
    except Exception as error:
        print("❌ Cannot read file:", error)
        return

    if not html.strip():
        print("❌ app.tl is empty.")
        return

    print()
    print("🚀 HazardStudio")
    print("━━━━━━━━━━━━━━━━━━━━")
    print(f"📄 File: {filename}")
    print(
        f"📦 HTML: "
        f"{len(html.encode('utf-8')) / 1024:.1f} KB"
    )
    print()

    site_name = input("you name site: ").strip().lower()

    if not valid_site_name(site_name):
        print("❌ Invalid site name.")
        print("Use only a-z, 0-9 and -")
        return

    print()
    print("📤 Uploading...")
    print("⏳ Please wait...")

    status, result = request_json(
        "/sites/create",
        {
            "api_key": config["api_key"],
            "site_name": site_name,
            "html": html,
        },
    )

    print()

    if not result.get("ok"):
        print("❌", result.get(
            "message",
            "Upload failed."
        ))
        return

    print("✅ Site published!")
    print(
        "🌐",
        result.get(
            "url",
            f"https://{site_name}.hazardstudio.ir"
        )
    )


def main():
    if len(sys.argv) < 2:
        print("HazardStudio CLI")
        print()
        print("Usage:")
        print("  hazardstudio login")
        print("  hazardstudio app.tl")
        return

    command = sys.argv[1]

    if command == "login":
        login()
        return

    if command.endswith(".tl"):
        deploy(command)
        return

    print("❌ Unknown command.")
    print()
    print("Usage:")
    print("  hazardstudio login")
    print("  hazardstudio app.tl")


if __name__ == "__main__":
    main()
