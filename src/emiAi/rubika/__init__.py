cat > src/emiAi/rubika/__init__.py <<'PY'
from .bot import EmiAi
from .decorators import message
from .buttons import button
from .reply import reply
from .keyboard import keyboard


__all__ = [
    "EmiAi",
    "message",
    "button",
    "reply",
    "keyboard",
]
PY
