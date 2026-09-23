_current_bot = None
_current_chat_id = None


def set_context(bot, chat_id):
    global _current_bot
    global _current_chat_id

    _current_bot = bot
    _current_chat_id = chat_id


def clear_context():
    global _current_bot
    global _current_chat_id

    _current_bot = None
    _current_chat_id = None


class Reply:

    def message(
        self,
        text,
        *components
    ):

        if _current_bot is None:
            raise RuntimeError(
                "reply.message() can only be used inside a message handler."
            )

        inline_keypad = None
        chat_keypad = None

        for component in components:

            if hasattr(component, "to_inline_dict"):
                inline_keypad = component.to_inline_dict()

            elif hasattr(component, "to_dict"):

                data = component.to_dict()

                if "rows" in data:

                    if "resize_keyboard" in data:
                        chat_keypad = data
                    else:
                        inline_keypad = data

        return _current_bot.send_message(
            _current_chat_id,
            text,
            inline_keypad=inline_keypad,
            chat_keypad=chat_keypad
        )


reply = Reply()
