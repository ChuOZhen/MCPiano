"""Integration tests for the Week 3 MCPiano toolchain tools.

Exercises ``esp32_upload``, ``esp32_execute``, ``esp32_reset`` and
``esp32_error`` against the real ESP32 on ``/dev/ttyACM0``.
"""

import asyncio
import os
import sys
import tempfile

sys.path.insert(0, "/home/chuzhen/MCPpiano/toolchain")

from tools.error_handler import esp32_error
from tools.executor import esp32_execute, esp32_reset
from tools.file_transfer import esp32_upload
from tools.serial_monitor import esp32_logs, esp32_serial


TEST_FILE = "_mcpiano_w3_test.py"
ERROR_FILE = "_mcpiano_w3_error.py"


async def test_upload():
    """Upload a simple MicroPython script to the ESP32."""
    print("[Test 1] Upload script to ESP32...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('print("MCPiano W3 upload OK")\n')
        local_path = f.name

    try:
        result = await esp32_upload(local_path, TEST_FILE)
        print("Result:", result)
        return result.get("success", False)
    finally:
        os.unlink(local_path)


async def test_execute():
    """Run the uploaded script and verify output in logs."""
    print("\n[Test 2] Execute uploaded script...")
    result = await esp32_execute(TEST_FILE, action="run")
    print("Result:", result)
    if not result.get("success"):
        return False

    # Give the board a moment to print.
    await esp32_serial("read", duration=2)
    logs = esp32_logs(lines=20, filter_str="MCPiano W3 upload OK")
    found = any("MCPiano W3 upload OK" in line for line in logs.get("logs", []))
    print("Output found in logs:", found)
    return found


async def test_error_reporting():
    """Upload and run a script that raises an exception, then parse it."""
    print("\n[Test 3] Error reporting...")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('raise ValueError("MCPiano W3 expected error")\n')
        local_path = f.name

    try:
        upload_result = await esp32_upload(local_path, ERROR_FILE)
        if not upload_result.get("success"):
            print("Upload failed:", upload_result)
            return False

        await esp32_execute(ERROR_FILE, action="run")
        await esp32_serial("read", duration=2)

        error_result = await esp32_error(auto_parse=True)
        print("Result:", error_result)
        error = error_result.get("error")
        return (
            error is not None
            and error.get("type") == "ValueError"
            and "MCPiano W3 expected error" in error.get("message", "")
        )
    finally:
        os.unlink(local_path)


async def test_reset():
    """Soft reset the ESP32 and verify boot message in logs."""
    print("\n[Test 4] Soft reset...")
    result = await esp32_reset(mode="soft")
    print("Result:", result)
    if not result.get("success"):
        return False

    # Wait for boot messages.
    await esp32_serial("read", duration=4)
    logs = esp32_logs(lines=30)
    boot_markers = ["rst:", "boot:", "entry 0x4"]
    found = any(
        any(marker in line for marker in boot_markers)
        for line in logs.get("logs", [])
    )
    print("Boot output found:", found)
    return found


async def cleanup():
    """Remove temporary files from the ESP32 filesystem."""
    print("\n[Cleanup] Removing test files from ESP32...")
    try:
        await esp32_execute("", action="stop")
    except Exception as exc:
        print("Stop failed (non-critical):", exc)


async def main():
    """Run all Week 3 toolchain integration tests."""
    print("=" * 50)
    print("Toolchain W3 Integration Test")
    print("=" * 50)

    results = {
        "upload": await test_upload(),
        "execute": await test_execute(),
        "error_reporting": await test_error_reporting(),
        "reset": await test_reset(),
    }
    await cleanup()

    print("\n" + "=" * 50)
    print("Test Results")
    print("=" * 50)
    for name, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  {name}: {status}")

    if all(results.values()):
        print("\nAll tests passed.")
    else:
        print("\nSome tests failed.")


if __name__ == "__main__":
    asyncio.run(main())
