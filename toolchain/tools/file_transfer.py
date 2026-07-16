"""File transfer helpers for the MCPiano ESP32 toolchain.

Implements ``esp32_upload`` and ``esp32_download`` as stubs for Week 3.
Actual raw-REPL based transfer will be implemented later.
"""


def esp32_upload(local_path: str, remote_path: str) -> dict:
    """Upload a local file to the ESP32 filesystem.

    Args:
        local_path: Path to the file on the host computer.
        remote_path: Destination path on the ESP32 filesystem.

    Returns:
        Dict with ``success`` and ``message`` keys.
    """
    return {"success": False, "message": "W3 实现"}


def esp32_download(remote_path: str, local_path: str) -> dict:
    """Download a file from the ESP32 filesystem.

    Args:
        remote_path: Source path on the ESP32 filesystem.
        local_path: Path to save the file on the host computer.

    Returns:
        Dict with ``success`` and ``message`` keys.
    """
    return {"success": False, "message": "W3 实现"}
