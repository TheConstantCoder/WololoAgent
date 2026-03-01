"""Push-to-Talk (PTT) hotkey listener.

Detects press and release events for the coaching hotkey.
"""

from typing import Callable
from pynput import keyboard


class HotkeyListener:
    """Listens for the PTT hotkey."""

    def __init__(self, on_press: Callable, on_release: Callable, key: str = "ctrl"):
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        self.ptt_key = self._parse_key(key)
        self.is_pressed = False
        self.listener = None

    def _parse_key(self, key_str: str):
        """Parse key string to pynput key."""
        if key_str == "ctrl":
            return keyboard.Key.ctrl
        elif key_str == "alt":
            return keyboard.Key.alt
        elif key_str == "shift":
            return keyboard.Key.shift
        return keyboard.KeyCode.from_char(key_str)

    def _on_press(self, key):
        """Internal callback for key press."""
        if key == self.ptt_key and not self.is_pressed:
            self.is_pressed = True
            self.on_press_callback()

    def _on_release(self, key):
        """Internal callback for key release."""
        if key == self.ptt_key and self.is_pressed:
            self.is_pressed = False
            self.on_release_callback()

    def start(self):
        """Start the keyboard listener."""
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.listener.start()

    def stop(self):
        """Stop the keyboard listener."""
        if self.listener:
            self.listener.stop()
