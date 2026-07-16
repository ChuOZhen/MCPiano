"""Standalone test for the toolchain serial monitor.

Imports ``toolchain.tools.serial_monitor`` directly and exercises the
``esp32_serial`` and ``esp32_logs`` APIs against the real ESP32 on
``/dev/ttyACM0``.
"""

import asyncio
import sys

sys.path.insert(0, "/home/chuzhen/MCPpiano/toolchain")

from tools.serial_monitor import esp32_serial, esp32_logs


async def test_serial_read():
    """Read ESP32 serial output for 5 seconds."""
    print("[Test 1] Read serial output for 5 seconds...")
    result = await esp32_serial("read", duration=5)
    print("Result:", result)
    return result.get("success", False)


async def test_serial_stop():
    """Stop the serial monitor."""
    print("\n[Test 2] Stop serial monitor...")
    result = await esp32_serial("stop")
    print("Result:", result)
    return result.get("success", False)


async def test_logs_retrieval():
    """Retrieve the most recent 50 log lines."""
    print("\n[Test 3] Retrieve recent logs...")
    result = esp32_logs(lines=50)
    print("Result:", result)
    return result.get("success", False)


async def main():
    """Run all serial monitor tests."""
    print("=" * 50)
    print("Toolchain Serial Monitor Test")
    print("=" * 50)

    results = {
        "serial_read": await test_serial_read(),
        "serial_stop": await test_serial_stop(),
        "logs_retrieval": await test_logs_retrieval(),
    }

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
