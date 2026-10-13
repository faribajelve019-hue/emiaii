"""EmiGram UserBot SDK.

Logs into the user's own EmiGram account over HTTPS.
Passwords are requested interactively and are never written to disk.
"""

from __future__ import annotations

import getpass
import time
from typing import Mapping

import requests


DEFAULT_BASE_URL = "https://hazardstudio.ir/Emigram/"


class Emigram:
    """Interactive login client for EmiGram account automation."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        poll_interval: float = 3.0,
        timeout: float = 15.0,
    ):
        self.base_url = base_url.rstrip("/") + "/"
        self.poll_interval = max(1.0, float(poll_interval))
        self.timeout = float(timeout)
        self.session = requests.Session()
        self.csrf = ""
        self.username = ""
        self.user_id = None
        self._logged_in = False

    def _url(self, action: str) -> str:
        return self.base_url + "?api=" + action

    def _get(self, action: str, **params):
        response = self.session.get(
            self._url(action),
            params=params,
            timeout=self.timeout,
        )
        try:
            data = response.json()
        except ValueError:
            raise RuntimeError(
                f"پاسخ سرور JSON معتبر نیست (HTTP {response.status_code})."
            )
        return response, data

    def _post(self, action: str, payload: dict):
        if not self.csrf:
            raise RuntimeError("توکن امنیتی موجود نیست؛ دوباره وارد شو.")

        response = self.session.post(
            self._url(action),
            json=payload,
            headers={"X-CSRF-Token": self.csrf},
            timeout=self.timeout,
        )
        try:
            data = response.json()
        except ValueError:
            raise RuntimeError(
                f"پاسخ سرور JSON معتبر نیست (HTTP {response.status_code})."
            )

        return response, data

    def login(self) -> bool:
        """Ask for account credentials and authenticate without saving password."""
        print("🤖 EmiGram UserBot")
        username = input("👤 نام کاربری حساب: ").strip()
        password = getpass.getpass("🔑 رمز عبور حساب: ")

        if not username or not password:
            print("❌ نام کاربری و رمز عبور الزامی هستند.")
            return False

        print("🔄 در حال بررسی اطلاعات...")

        try:
            # The server creates a CSRF token for this session.
            response, initial = self._get("me")

            self.csrf = str(initial.get("csrf") or "")
            if not self.csrf:
                print(
                    "❌ سرور توکن امنیتی ورود را برنگرداند. "
                    "API me را بررسی کن."
                )
                return False

            response, data = self._post(
                "login",
                {"username": username, "password": password},
            )

            if response.status_code != 200 or not data.get("ok"):
                print(
                    "❌ " + str(
                        data.get(
                            "error",
                            "نام کاربری یا رمز عبور اشتباه است."
                        )
                    )
                )
                return False

            self.username = str(data.get("username") or username)
            self.csrf = str(data.get("csrf") or self.csrf)
            self._logged_in = True

            print(f"✅ ورود موفق بود: {self.username}")
            print("🔐 رمز عبور در فایل ذخیره نمی‌شود.")
            return True

        except requests.RequestException as exc:
            print(f"❌ اتصال به EmiGram ناموفق بود: {exc}")
            return False
        finally:
            # Avoid retaining the local variable longer than necessary.
            password = None

    def run(self, bot_message: Mapping[str, str]):
        """Start auto-reply polling after the server's bot_updates API exists.

        Rule keys are matched as case-insensitive substrings.
        """
        if not isinstance(bot_message, Mapping):
            raise TypeError("bot_message باید دیکشنری یا Mapping باشد.")

        rules = {}
        for key, value in bot_message.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise TypeError("کلیدها و پاسخ‌ها باید رشته باشند.")
            key = key.strip()
            value = value.strip()
            if key and value:
                rules[key.casefold()] = value

        if not rules:
            raise ValueError("حداقل یک قانون پاسخ خودکار تعریف کن.")

        if not self._logged_in:
            if not self.login():
                return

        print("🔄 در حال بررسی API دریافت پیام‌ها...")

        try:
            response, data = self._get("bot_updates", after=0)
            if response.status_code == 404 or data.get("error") == "unknown_action":
                print(
                    "⚠️ ورود موفق است، اما API دریافت پیام‌ها هنوز در "
                    "app.php نصب نشده است؛ فعلاً پاسخ خودکار فعال نمی‌شود."
                )
                print(
                    "مسیر لازم: GET ?api=bot_updates&after=ID "
                    "با احراز هویت و فقط پیام‌های دریافتی حساب."
                )
                return

            if response.status_code != 200 or not data.get("ok"):
                print("❌ دریافت پیام‌ها ناموفق بود:", data.get("error"))
                return

            cursor = int(data.get("latest_id", 0))
            print("✅ UserBot فعال شد. برای توقف Ctrl+C بزن.")
            print("ℹ️ برای جلوگیری از پاسخ به پیام‌های قدیمی، "
                  "از این لحظه پیام‌های جدید بررسی می‌شوند.")

            while True:
                response, data = self._get("bot_updates", after=cursor)

                if response.status_code != 200 or not data.get("ok"):
                    if response.status_code in (401, 403):
                        print("❌ نشست حساب منقضی یا دسترسی محدود شده است.")
                        return
                    print("⚠️ خطای دریافت پیام؛ تلاش دوباره...")
                    time.sleep(self.poll_interval)
                    continue

                messages = data.get("messages", [])
                for message in messages:
                    message_id = int(message.get("id", 0))
                    if message_id <= cursor:
                        continue

                    # Advance cursor even when no rule matches.
                    cursor = message_id
                    body = str(message.get("body", "")).strip()
                    receiver_id = message.get("sender_id")

                    if not body or not receiver_id:
                        continue

                    normalized = body.casefold()
                    answer = next(
                        (
                            reply for keyword, reply in rules.items()
                            if keyword in normalized
                        ),
                        None,
                    )

                    if answer is None:
                        continue

                    try:
                        sent_response, sent = self._post(
                            "send",
                            {
                                "receiver_id": int(receiver_id),
                                "body": answer,
                            },
                        )

                        if sent_response.status_code == 200 and sent.get("ok"):
                            print(f"📨 پاسخ ارسال شد به شناسه {receiver_id}")
                        else:
                            print(
                                "⚠️ پاسخ ارسال نشد:",
                                sent.get("error", sent_response.status_code),
                            )
                    except (requests.RequestException, ValueError) as exc:
                        print("⚠️ خطا در ارسال پاسخ:", exc)

                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            print("\n🛑 UserBot متوقف شد.")
        except requests.RequestException as exc:
            print("❌ خطای اتصال:", exc)
        finally:
            self.session.close()
            self._logged_in = False
