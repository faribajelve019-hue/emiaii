class ChatKeyboard:

    def __init__(
        self,
        *buttons,
        resize=True,
        on_time=False
    ):
        self.buttons = buttons
        self.resize = resize
        self.on_time = on_time

    def to_dict(self):

        rows = []

        for item in self.buttons:

            if isinstance(item, (list, tuple)):

                row = []

                for text in item:
                    row.append({
                        "id": text,
                        "type": "Simple",
                        "button_text": text
                    })

                rows.append({
                    "buttons": row
                })

            else:

                rows.append({
                    "buttons": [
                        {
                            "id": item,
                            "type": "Simple",
                            "button_text": item
                        }
                    ]
                })

        return {
            "rows": rows,
            "resize_keyboard": self.resize,
            "on_time_keyboard": self.on_time
        }


def keyboard(*buttons):
    return ChatKeyboard(*buttons)
