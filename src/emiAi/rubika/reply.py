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

        inline_buttons = []
        chat_keypad = None

        for component in components:

            # -----------------------------
            # INLINE
            # -----------------------------

            if hasattr(
                component,
                "to_inline_dict"
            ):

                data = component.to_inline_dict()

                rows = data.get(
                    "rows",
                    []
                )

                for row in rows:

                    buttons = row.get(
                        "buttons",
                        []
                    )

                    inline_buttons.extend(
                        buttons
                    )

            # -----------------------------
            # CHAT KEYBOARD
            # -----------------------------

            elif hasattr(
                component,
                "to_dict"
            ):

                data = component.to_dict()

                if (
                    "resize_keyboard"
                    in data
                ):

                    chat_keypad = data

        inline_keypad = None

        if inline_buttons:

            inline_keypad = {
                "rows": [
                    {
                        "buttons": inline_buttons
                    }
                ]
            }

        return _current_bot.send_message(
            _current_chat_id,
            text,
            inline_keypad=inline_keypad,
            chat_keypad=chat_keypad
        )


reply = Reply()
