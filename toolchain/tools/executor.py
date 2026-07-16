"""Program execution and reset helpers for the MCPiano ESP32 toolchain.

Implements ``esp32_execute`` and ``esp32_reset`` as stubs for Week 3.
"""


def esp32_execute(entry_file: str, action: str = "run") -> dict:
    """Execute a MicroPython file on the ESP32.

    Args:
        entry_file: Name of the file to execute on the ESP32.
        action: One of ``"run"`` or ``"stop"``.

    Returns:
        Dict with ``success`` and ``message`` keys.
    """
    return {"success": False, "message": "W3 实现"}


def esp32_reset(mode: str = "soft") -> dict:
    """Reset the ESP32 microcontroller.

    Args:
        mode: ``"soft"`` for a software reset via REPL, ``"hard"`` for
            toggling DTR/RTS lines.

    Returns:
        Dict with ``success`` and ``message`` keys.
    """
    return {"success": False, "message": "W3 实现"}
