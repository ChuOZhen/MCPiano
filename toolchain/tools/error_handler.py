"""Error reporting helper for the MCPiano ESP32 toolchain.

Implements ``esp32_error`` as a stub for Week 3.  The final version will
parse recent serial output for MicroPython tracebacks.
"""


def esp32_error(auto_parse: bool = True) -> dict:
    """Parse recent serial output for MicroPython errors.

    Args:
        auto_parse: If True, automatically detect Traceback blocks.

    Returns:
        Dict with detected error information or a placeholder message.
    """
    return {"success": False, "message": "W3 实现"}
