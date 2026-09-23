from .decorators import button as button_decorator


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

    def __init__(self, text, callback):
        self.button = InlineButton(
            text,
            callback
        )

    def to_inline_dict(self):
        return {
            "rows": [
                {
                    "buttons": [
                        self.button.to_dict()
                    ]
                }
            ]
        }


class Button:

    def __call__(self, callback):
        return button_decorator(callback)

    def inline(self, text, callback):
        return InlineKeyboard(
            text,
            callback
        )


button = Button()
