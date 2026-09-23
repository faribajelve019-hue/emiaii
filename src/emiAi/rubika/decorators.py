_handlers = {}
_button_handlers = {}


def message(command):
    if not isinstance(command, str):
        raise TypeError("message() command must be a string")

    def decorator(function):
        _handlers[command] = function
        return function

    return decorator


def button(callback):
    if not isinstance(callback, str):
        raise TypeError("button() callback must be a string")

    def decorator(function):
        _button_handlers[callback] = function
        return function

    return decorator


def get_message_handlers():
    return _handlers


def get_button_handlers():
    return _button_handlers
