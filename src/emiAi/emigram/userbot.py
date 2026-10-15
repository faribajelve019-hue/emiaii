"""EmiGram account UserBot SDK with message and callback decorators."""

from __future__ import annotations

import getpass
import time
from collections.abc import Mapping
from typing import Any

import requests

DEFAULT_BASE_URL = "https://www.emigram.ir/web-acconts/"


class Message:
    def __init__(self, bot, data):
        self._bot = bot
        self._data = dict(data)
        self.id = int(data.get("id", 0))
        self.sender_id = int(data.get("sender_id", 0))
        self.receiver_id = int(data.get("receiver_id", 0))
        self.body = str(data.get("body", ""))
        self.created_at = str(data.get("created_at", ""))

    def reply(self, text: str, buttons=None):
        """Reply to the sender. Button items are (callback_data, label)."""
        return self._bot.send(
            receiver_id=self.sender_id,
            body=text,
            buttons=buttons,
        )


class CallbackEvent:
    def __init__(self, bot, data):
        self._bot = bot
        self._data = dict(data)
        self.id = int(data.get("id", 0))
        self.user_id = int(data.get("clicker_id", 0))
        self.clicker_id = self.user_id
        self.message_id = int(data.get("message_id", 0))
        self.callback_data = str(data.get("callback_data", ""))
        self.created_at = str(data.get("created_at", ""))

    def reply(self, text: str, buttons=None):
        """Send a message to the user who clicked the button."""
        return self._bot.send(
            receiver_id=self.user_id,
            body=text,
            buttons=buttons,
        )


class Emigram:
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
        self._message_handlers = []
        self._callback_handlers = {}

    def message(self, commands):
        """Register one or more substring triggers."""
        if isinstance(commands, str):
            commands = [commands]

        if not isinstance(commands, (list, tuple, set)):
            raise TypeError("message باید رشته یا لیستی از رشته‌ها باشد.")

        commands = list(commands)
        if not commands or any(not isinstance(x, str) or not x.strip()
                               for x in commands):
            raise ValueError("عبارت‌های پیام نامعتبر هستند.")

        def decorator(function):
            for command in commands:
                self._message_handlers.append(
                    (command.strip().casefold(), function)
                )
            return function

        return decorator

    def callback(self, callback_data: str):
        """Register an exact callback_data handler."""
        if not isinstance(callback_data, str):
            raise TypeError("callback باید رشته باشد.")

        callback_data = callback_data.strip()
        if not callback_data:
            raise ValueError("callback نمی‌تواند خالی باشد.")

        def decorator(function):
            self._callback_handlers[callback_data] = function
            return function

        return decorator

    def _url(self, action):
        return self.base_url + "?api=" + action

    def _get(self, action, **params):
        response = self.session.get(
            self._url(action),
            params=params,
            timeout=self.timeout,
        )
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"پاسخ سرور JSON معتبر نیست (HTTP {response.status_code})."
            ) from exc
        return response, data

    def _post(self, action, payload):
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
        except ValueError as exc:
            raise RuntimeError(
                f"پاسخ سرور JSON معتبر نیست (HTTP {response.status_code})."
            ) from exc

        if data.get("csrf"):
            self.csrf = str(data["csrf"])

        return response, data

    def login(self):
        print("🤖 EmiGram UserBot")
        username = input("👤 نام کاربری حساب: ").strip()
        password = getpass.getpass("🔑 رمز عبور حساب: ")

        if not username or not password:
            print("❌ نام کاربری و رمز عبور الزامی هستند.")
            return False

        try:
            response, initial = self._get("me")
            self.csrf = str(initial.get("csrf") or "")

            if response.status_code != 200 or not self.csrf:
                print("❌ دریافت توکن امنیتی ناموفق بود.")
                return False

            response, data = self._post(
                "login",
                {"username": username, "password": password},
            )

            if response.status_code != 200 or not data.get("ok"):
                print("❌", data.get("error", "ورود ناموفق بود."))
                return False

            self.username = str(data.get("username") or username)
            self.csrf = str(data.get("csrf") or self.csrf)
            self._logged_in = True

            print(f"✅ ورود موفق: {self.username}")
            print("🔐 رمز عبور در فایل ذخیره نمی‌شود.")
            return True

        except requests.RequestException as exc:
            print("❌ خطای اتصال:", exc)
            return False
        finally:
            password = None

    @staticmethod
    def _normalize_buttons(buttons):
        if buttons is None:
            return []

        if not isinstance(buttons, (list, tuple)):
            raise TypeError("buttons باید لیست یا تاپل باشد.")

        if len(buttons) > 8:
            raise ValueError("حداکثر ۸ دکمه مجاز است.")

        result = []

        for item in buttons:
            if isinstance(item, Mapping):
                callback_data = item.get("callback_data")
                label = item.get("label")
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                callback_data, label = item
            else:
                raise ValueError(
                    "هر دکمه باید (callback_data, label) باشد."
                )

            if not isinstance(callback_data, str) or not isinstance(label, str):
                raise TypeError("شناسه و عنوان دکمه باید رشته باشند.")

            callback_data = callback_data.strip()
            label = label.strip()

            import re
            if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,64}", callback_data):
                raise ValueError("شناسه دکمه نامعتبر است.")

            if not label or len(label) > 40:
                raise ValueError("عنوان دکمه باید ۱ تا ۴۰ کاراکتر باشد.")

            result.append({
                "callback_data": callback_data,
                "label": label,
            })

        return result

    def send(self, receiver_id: int, body: str, buttons=None):
        """Send a message, optionally with inline callback buttons."""
        if not isinstance(body, str) or not body.strip():
            raise ValueError("متن پیام نمی‌تواند خالی باشد.")

        payload = {
            "receiver_id": int(receiver_id),
            "body": body.strip(),
        }

        normalized = self._normalize_buttons(buttons)
        if normalized:
            payload["buttons"] = normalized

        response, data = self._post("send", payload)

        if response.status_code != 200 or not data.get("ok"):
            raise RuntimeError(
                str(data.get("error", f"HTTP {response.status_code}"))
            )

        return data

    def _dispatch_message(self, raw_message, rules):
        message = Message(self, raw_message)
        body = message.body.casefold()

        for trigger, handler in self._message_handlers:
            if trigger in body:
                try:
                    handler(message)
                except Exception as exc:
                    print("⚠️ خطای handler پیام:", exc)
                break

        # سازگاری با شیوه قدیمی bot.run({...})
        if rules:
            answer = next(
                (reply for key, reply in rules.items() if key in body),
                None,
            )
            if answer:
                try:
                    message.reply(answer)
                except Exception as exc:
                    print("⚠️ ارسال پاسخ ناموفق بود:", exc)

    def _dispatch_callback(self, raw_event):
        event = CallbackEvent(self, raw_event)
        handler = self._callback_handlers.get(event.callback_data)

        if handler is None:
            return

        try:
            handler(event)
        except Exception as exc:
            print("⚠️ خطای handler دکمه:", exc)

    def run(self, bot_message=None):
        """Run decorator handlers or legacy run({'hello': 'hi'})."""
        rules = {}

        if bot_message is not None:
            if not isinstance(bot_message, Mapping):
                raise TypeError("bot_message باید دیکشنری یا Mapping باشد.")

            for key, value in bot_message.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise TypeError("کلیدها و پاسخ‌ها باید رشته باشند.")

                key, value = key.strip().casefold(), value.strip()
                if key and value:
                    rules[key] = value

        if not rules and not self._message_handlers and not self._callback_handlers:
            raise ValueError(
                "ابتدا @bot.message یا @bot.callback تعریف کن."
            )

        if not self._logged_in and not self.login():
            return

        try:
            response, data = self._get("bot_updates", after=0)
            if response.status_code != 200 or not data.get("ok"):
                print("❌ API پیام‌ها در دسترس نیست:", data.get("error"))
                return

            message_cursor = int(data.get("latest_id", 0))

            response, data = self._get("bot_callbacks", after=0)
            if response.status_code != 200 or not data.get("ok"):
                print("❌ API کلیک‌ها در دسترس نیست:", data.get("error"))
                print("ℹ️ ابتدا تغییرات PHP را روی سرور نصب کن.")
                return

            callback_cursor = int(data.get("latest_id", 0))

            print("✅ EmiGram UserBot فعال شد.")
            print("🛑 برای توقف Ctrl+C بزن.")

            while True:
                try:
                    response, data = self._get(
                        "bot_updates", after=message_cursor
                    )

                    if response.status_code in (401, 403):
                        print("❌ نشست منقضی شده یا دسترسی محدود است.")
                        return

                    if response.status_code == 200 and data.get("ok"):
                        for raw in data.get("messages", []):
                            message_id = int(raw.get("id", 0))
                            if message_id <= message_cursor:
                                continue

                            message_cursor = message_id

                            if int(raw.get("receiver_id", 0)) != int(
                                self.user_id or raw.get("receiver_id", 0)
                            ):
                                # سرور خودش پیام‌های حساب را فیلتر می‌کند.
                                pass

                            self._dispatch_message(raw, rules)
                    else:
                        print("⚠️ دریافت پیام ناموفق بود.")

                except requests.RequestException as exc:
                    print("⚠️ خطای دریافت پیام:", exc)

                try:
                    response, data = self._get(
                        "bot_callbacks", after=callback_cursor
                    )

                    if response.status_code in (401, 403):
                        print("❌ نشست حساب منقضی شده است.")
                        return

                    if response.status_code == 200 and data.get("ok"):
                        for raw in data.get("callbacks", []):
                            event_id = int(raw.get("id", 0))
                            if event_id <= callback_cursor:
                                continue

                            callback_cursor = event_id
                            self._dispatch_callback(raw)
                    else:
                        print("⚠️ دریافت کلیک‌ها ناموفق بود.")

                except requests.RequestException as exc:
                    print("⚠️ خطای دریافت کلیک:", exc)

                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            print("\n🛑 EmiGram UserBot متوقف شد.")
        finally:
            self.session.close()
            self._logged_in = False
