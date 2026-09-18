import requests


class EmiAI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://emiai.pythonanywhere.com/v1/chat/completions"

    def chat(self, message):
        response = requests.post(
            self.url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "model": "Emi-o-mini/free",
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
                f"EmiAI API returned non-JSON response.\n"
                f"HTTP Status: {response.status_code}\n"
                f"Response:\n{response.text[:2000]}"
            )

        if response.status_code == 200:
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError):
                raise Exception(
                    f"Invalid EmiAI API response:\n{data}"
                )

        raise Exception(
            f"EmiAI API Error ({response.status_code}):\n{data}"
        )
