"""System-wide keyboard shortcut for the Windows version (works while another program, such as an emulator, has the focus).

The shortcut is registered with the Windows API (RegisterHotKey) in its own thread. Windows keeps the key for itself while
the shortcut is registered, so the program that has the focus does not receive it. Only used by app.py."""

import ctypes
import os
import threading

_WM_HOTKEY = 0x0312
_WM_QUIT = 0x0012
_MODIFIERS = {"Alt": 0x1, "Control": 0x2, "Shift": 0x4}
_MOD_NOREPEAT = 0x4000                     # holding the keys down triggers the shortcut only once
_HOTKEY_ID = 1


def parse(seq):
    """(modifiers, virtual key code) of a Tk sequence such as 'F5' or 'Control-Alt-r', or None if unsupported."""
    parts = str(seq).split("-")
    key, mods = parts[-1], 0
    for p in parts[:-1]:
        if p not in _MODIFIERS:
            return None
        mods |= _MODIFIERS[p]
    if len(key) > 1 and key[0] == "F" and key[1:].isdigit() and 1 <= int(key[1:]) <= 12:
        return mods, 0x70 + int(key[1:]) - 1       # VK_F1 = 0x70
    if len(key) == 1 and key.isascii() and key.isalnum():
        return mods, ord(key.upper())              # letters and digits: virtual key = ASCII code
    return None


class GlobalHotkey:
    """One global shortcut. `callback()` is called from a background thread each time it is pressed."""

    def __init__(self, callback):
        self.callback = callback
        self._thread = None
        self._thread_id = None

    def register(self, seq):
        """Replace the current shortcut by `seq` (Tk sequence). Return False if it is unsupported or already used."""
        self.unregister()
        parsed = parse(seq)
        if os.name != "nt" or parsed is None:
            return False
        result = {"ok": False}
        ready = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(parsed, result, ready), daemon=True)
        self._thread.start()
        ready.wait(2)
        if not result["ok"]:
            self._thread = None
        return result["ok"]

    def unregister(self):
        """Release the shortcut (if any)."""
        thread, tid = self._thread, self._thread_id
        self._thread = self._thread_id = None
        if thread is not None and tid:
            ctypes.windll.user32.PostThreadMessageW(tid, _WM_QUIT, 0, 0)
            thread.join(1)

    def _run(self, parsed, result, ready):
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        msg = wintypes.MSG()
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 0)         # creates the message queue of this thread
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        mods, vk = parsed
        result["ok"] = bool(user32.RegisterHotKey(None, _HOTKEY_ID, mods | _MOD_NOREPEAT, vk))
        ready.set()
        if not result["ok"]:
            return
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == _WM_HOTKEY:
                    try:
                        self.callback()
                    except Exception:
                        pass
        finally:
            user32.UnregisterHotKey(None, _HOTKEY_ID)
