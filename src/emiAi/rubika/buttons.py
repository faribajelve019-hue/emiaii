class InlineButton:

    def __init__(self, text, callback):
        self.text = text
        self.callback = callback

    def to_dict(self):
        return {
            "id": self.callback,
            "type": "Simple",
            "button_text": self.text
        }


class InlineKeyboard:

    def __init__(self, buttons):
        self.buttons = buttons

    def to_inline_dict(self):

        return {
            "rows": [
                {
                    "buttons": [
                        button.to_dict()
                        for button in self.buttons
                    ]
                }
            ]
        }


class Button:

    @staticmethod
    def inline(text, callback):
        return InlineKeyboard([
            InlineButton(text, callback)
        ])


button = Button()
