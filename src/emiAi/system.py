import requests


class _Message:

    def __init__(self, system):
        self.system = system
        self._user_messages = set()

    @property
    def user(self):
        return self._user_messages

    @user.setter
    def user(self, value):

        if isinstance(value, str):
            value = {value}

        if not isinstance(value, (set, list, tuple)):
            raise TypeError(
                "emisystem.message.user must be "
                "a set, list, tuple or string."
            )

        messages = set()

        for message in value:

            if not isinstance(message, str):
                raise TypeError(
                    "Every user message must be a string."
                )

            message = message.strip()

            if message:
                messages.add(message)

        self._user_messages = messages


class _Answer:

    def __init__(self, system):
        self.system = system

    def message(self, answer):

        if not isinstance(answer, str):
            raise TypeError(
                "emisystem.answer.message() "
                "must receive a string."
            )

        self.system._answer_message = answer

        # ساخت Rule برای پیام‌های فعلی
        for user_message in self.system.message.user:
            self.system._rules[user_message] = answer

        return answer


class _Data:

    def __init__(self, system):
        self.system = system
        self.limit = None

    def __getitem__(self, value):

        if not isinstance(value, int):
            raise TypeError(
                "emisystem.Data[] must contain an integer."
            )

        if value <= 0:
            raise ValueError(
                "Daily message limit must be greater than 0."
            )

        self.limit = value
        self.system.daily_limit = value

        return value


class EmiSystem:

    def __init__(self, api_key):

        self.api_key = api_key

        self.url = (
            "https://emiai.pythonanywhere.com/"
            "v1/chat/completions"
        )

        self.model = None
        self.daily_limit = None

        # Message system
        self.message = _Message(self)
        self.answer = _Answer(self)

        # ذخیره Rule ها
        self._rules = {}

        # پاسخ آخرین Rule
        self._answer_message = None

        # Data system
        self.Data = _Data(self)

    # ==========================================
    # Model Setting
    # ==========================================

    def setting(self, model):

        def decorator(function):

            self.model = model

            try:

                response = requests.post(
                    self.url,

                    headers={
                        "Authorization":
                            f"Bearer {self.api_key}",

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    },

                    json={
                        "model": self.model,

                        "messages": [
                            {
                                "role": "user",
                                "content": "ping"
                            }
                        ]
                    },

                    timeout=30
                )

                if response.status_code == 401:

                    raise ValueError(
                        "Invalid EmiAI API key."
                    )

                if response.status_code == 400:

                    try:

                        data = response.json()

                        message = data.get(
                            "error",
                            {}
                        ).get(
                            "message",
                            "Invalid model."
                        )

                    except Exception:

                        message = "Invalid model."

                    raise ValueError(
                        f"Model verification failed: {message}"
                    )

            except requests.RequestException as e:

                raise ConnectionError(
                    f"EmiAI connection failed: {e}"
                )

            return function

        return decorator

    # ==========================================
    # Chat
    # ==========================================

    def chat(self, message):

        if not isinstance(message, str):

            raise TypeError(
                "emisystem.chat() "
                "message must be a string."
            )

        # ======================================
        # بررسی Message Rules
        # ======================================

        user_message = message.strip()

        if user_message in self._rules:

            return self._rules[user_message]

        # ======================================
        # اگر Rule نبود → استفاده از AI
        # ======================================

        if not self.model:

            raise ValueError(
                "No model configured. "
                "Use @emisystem.setting('model')."
            )

        response = requests.post(

            self.url,

            headers={
                "Authorization":
                    f"Bearer {self.api_key}",

                "Content-Type":
                    "application/json",

                "Accept":
                    "application/json"
            },

            json={
                "model": self.model,

                "messages": [
                    {
                        "role": "user",
                        "content": message
                    }
                ]
            },

            timeout=60
        )

        try:

            data = response.json()

        except ValueError:

            raise Exception(
                "EmiAI API returned non-JSON response."
            )

        if response.status_code == 200:

            try:

                return data[
                    "choices"
                ][0][
                    "message"
                ][
                    "content"
                ]

            except (
                KeyError,
                IndexError,
                TypeError
            ):

                raise Exception(
                    f"Invalid EmiAI API response:\n{data}"
                )

        raise Exception(
            f"EmiAI API Error "
            f"({response.status_code}):\n{data}"
        )
