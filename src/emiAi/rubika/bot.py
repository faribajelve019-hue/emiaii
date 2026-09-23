import time
import requests

from .decorators import (
    get_message_handlers,
    get_button_handlers
)

from .reply import (
    set_context,
    clear_context
)


class EmiAi:

    def __init__(
        self,
        token,
        gateway="https://bot.hazardstudio.ir/index.php"
    ):
        if not isinstance(token, str) or not token.strip():
            raise ValueError(
                "Rubika bot token is required."
            )

        self.token = token.strip()
        self.gateway = gateway
        self.running = False
        self.offset_id = None
        self.last_message_id = None

    def request(self, action, **data):

        payload = {
            "action": action,
            "token": self.token
        }

        payload.update(data)

        try:
            response = requests.post(
                self.gateway,
                json=payload,
                timeout=40
            )
        except requests.RequestException as e:
            raise RuntimeError(
                f"Gateway connection error: {e}"
            )

        try:
            result = response.json()
        except ValueError:
            raise RuntimeError(
                "Gateway returned invalid JSON:\n"
                + response.text[:2000]
            )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Gateway HTTP error:\n{result}"
            )

        return result

    def send_message(
        self,
        chat_id,
        text,
        inline_keypad=None,
        chat_keypad=None,
        chat_keypad_type="New"
    ):

        data = {
            "chat_id": chat_id,
            "text": text
        }

        if inline_keypad is not None:
            data["inline_keypad"] = inline_keypad

        if chat_keypad is not None:
            data["chat_keypad"] = chat_keypad
            data["chat_keypad_type"] = chat_keypad_type

        return self.request(
            "sendMessage",
            **data
        )

    def get_updates(self):

        data = {
            "limit": 50
        }

        if self.offset_id is not None:
            data["offset_id"] = self.offset_id

        print(
            "GET UPDATES | offset_id =",
            self.offset_id
        )

        return self.request(
            "rubika",
            method="getUpdates",
            data=data
        )

    def extract_data(self, result):

        if not isinstance(result, dict):
            return None

        gateway_data = result.get("data")

        if not isinstance(gateway_data, dict):
            return None

        rubika_data = gateway_data.get("data")

        if not isinstance(rubika_data, dict):
            return None

        return rubika_data

    def get_latest_message(self, updates):

        if not isinstance(updates, list):
            return None

        messages = []

        for update in updates:

            if not isinstance(update, dict):
                continue

            if update.get("type") != "NewMessage":
                continue

            message = update.get("new_message")

            if not isinstance(message, dict):
                continue

            chat_id = update.get("chat_id")

            if not chat_id:
                continue

            messages.append(
                (update, message)
            )

        if not messages:
            return None

        messages.sort(
            key=lambda item: int(
                item[0].get(
                    "update_time",
                    0
                )
            )
        )

        return messages[-1]

    def process_update(self, result):

        rubika_data = self.extract_data(result)

        if rubika_data is None:
            print("Invalid Rubika response")
            return

        updates = rubika_data.get(
            "updates",
            []
        )

        next_offset = rubika_data.get(
            "next_offset_id"
        )

        print(
            "UPDATES:",
            len(updates)
        )

        print(
            "NEXT OFFSET:",
            next_offset
        )

        if next_offset:
            self.offset_id = next_offset

        if not updates:
            return

        latest = self.get_latest_message(
            updates
        )

        if latest is None:
            return

        update, message = latest

        chat_id = update.get("chat_id")

        message_id = message.get(
            "message_id"
        )

        text = (
            message.get("text")
            or ""
        ).strip()

        if (
            message_id
            and
            message_id == self.last_message_id
        ):
            print(
                "Duplicate message ignored:",
                message_id
            )
            return

        if message_id:
            self.last_message_id = message_id

        aux_data = message.get(
            "aux_data"
        )

        if isinstance(aux_data, dict):

            callback = aux_data.get(
                "button_id"
            )

            if callback:

                print(
                    "LATEST INLINE:",
                    callback
                )

                handler = (
                    get_button_handlers()
                    .get(callback)
                )

                if handler is None:

                    print(
                        "No inline handler:",
                        callback
                    )

                    return

                set_context(
                    self,
                    chat_id
                )

                try:
                    handler()
                finally:
                    clear_context()

                return

        handler = (
            get_message_handlers()
            .get(text)
        )

        if handler is None:

            print(
                "No message handler:",
                repr(text)
            )

            return

        print(
            "LATEST MESSAGE:",
            repr(text)
        )

        set_context(
            self,
            chat_id
        )

        try:
            handler()
        finally:
            clear_context()

    def run(self):

        self.running = True

        print(
            "================================"
        )
        print(
            "emiAi Rubika Bot"
        )
        print(
            "================================"
        )
        print(
            "Gateway:",
            self.gateway
        )
        print(
            "Bot started."
        )
        print(
            "Waiting for latest updates..."
        )
        print()

        while self.running:

            try:

                result = self.get_updates()

                self.process_update(
                    result
                )

                time.sleep(1)

            except KeyboardInterrupt:

                self.running = False

                print(
                    "\nBot stopped."
                )

            except Exception as e:

                print(
                    "emiAi Error:",
                    repr(e)
                )

                time.sleep(5)

    def stop(self):

        self.running = False
