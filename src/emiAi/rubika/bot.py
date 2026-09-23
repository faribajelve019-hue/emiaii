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
        gateway="https://bot.hazardstudio.ir/api.php",
        secret=None
    ):

        if not isinstance(token, str) or not token.strip():
            raise ValueError(
                "Rubika bot token is required."
            )

        self.token = token.strip()

        self.gateway = gateway

        self.secret = secret

        self.running = False

        self.last_message_id = None

    # ==================================================
    # GATEWAY REQUEST
    # ==================================================

    def request(self, action, **data):

        payload = {
            "action": action,
            "token": self.token
        }

        payload.update(data)

        headers = {
            "Content-Type": "application/json"
        }

        if self.secret:
            headers["X-EmiAI-Secret"] = self.secret

        try:

            response = requests.post(
                self.gateway,
                json=payload,
                headers=headers,
                timeout=40
            )

        except requests.RequestException as e:

            raise RuntimeError(
                f"emiAi Gateway connection error: {e}"
            )

        try:

            result = response.json()

        except ValueError:

            raise RuntimeError(
                "emiAi Gateway returned invalid JSON:\n"
                + response.text[:2000]
            )

        if response.status_code >= 400:

            raise RuntimeError(
                f"emiAi Gateway error:\n{result}"
            )

        return result

    # ==================================================
    # SEND MESSAGE
    # ==================================================

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

    # ==================================================
    # GET UPDATES
    # ==================================================

    def get_updates(self):

        return self.request(
            "getUpdates"
        )

    # ==================================================
    # USER INFO
    # ==================================================

    def get_user_info(self, user_guid):

        result = self.request(
            "getUserInfo",
            user_guid=user_guid
        )

        return result

    # ==================================================
    # PROCESS UPDATE
    # ==================================================

    def process_update(self, result):

        if not isinstance(result, dict):
            return

        updates = result.get("data", result)

        if isinstance(updates, dict):

            if "update" in updates:
                updates = [updates]

            elif "inline_message" in updates:
                updates = [updates]

            else:
                updates = [updates]

        if not isinstance(updates, list):
            return

        for item in updates:

            self._process_single_update(item)

    # ==================================================
    # SINGLE UPDATE
    # ==================================================

    def _process_single_update(self, update):

        if not isinstance(update, dict):
            return

        # ----------------------------------------------
        # NORMAL MESSAGE
        # ----------------------------------------------

        data = update.get("update")

        if isinstance(data, dict):

            update_type = data.get("type")

            if update_type != "NewMessage":
                return

            chat_id = data.get("chat_id")

            message = data.get(
                "new_message",
                {}
            )

            text = (
                message.get("text")
                or ""
            ).strip()

            sender_id = (
                message.get("sender_id")
                or ""
            )

            if not chat_id:
                return

            handlers = get_message_handlers()

            handler = handlers.get(text)

            if handler is None:
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

        # ----------------------------------------------
        # INLINE BUTTON
        # ----------------------------------------------

        inline = update.get(
            "inline_message"
        )

        if isinstance(inline, dict):

            chat_id = inline.get(
                "chat_id"
            )

            sender_id = inline.get(
                "sender_id"
            )

            aux_data = inline.get(
                "aux_data",
                {}
            )

            callback = aux_data.get(
                "button_id"
            )

            if not chat_id or not callback:
                return

            handlers = get_button_handlers()

            handler = handlers.get(callback)

            if handler is None:
                return

            set_context(
                self,
                chat_id
            )

            try:

                handler()

            finally:

                clear_context()

    # ==================================================
    # RUN
    # ==================================================

    def run(self):

        self.running = True

        print(
            "emiAi Rubika Bot started..."
        )

        print(
            "Gateway:",
            self.gateway
        )

        print(
            "Waiting for messages..."
        )

        while self.running:

            try:

                result = self.get_updates()

                self.process_update(
                    result
                )

                time.sleep(2)

            except KeyboardInterrupt:

                self.running = False

                print(
                    "\nemiAi Rubika Bot stopped."
                )

            except Exception as e:

                print(
                    "emiAi Error:",
                    e
                )

                time.sleep(5)

    # ==================================================
    # STOP
    # ==================================================

    def stop(self):

        self.running = False
