# desky-ble

Unofficial Python library for local Bluetooth LE control of Desky® Standing Desks.

This standalone client library provides a robust, asynchronous interface for interacting with Desky desk controllers. It handles all low-level BLE communication, including real-time height monitoring, preset management, and automatic detection of common controller variants (specifically those utilizing Lierda and Peilin chipsets).

Designed for interoperability, this library is built to integrate seamlessly with platforms like Home Assistant, enabling local, cloud-free automation of your workspace.

## Supported controllers

| Variant  | BLE Service UUID                         |
|----------|------------------------------------------|
| Lierda 1 | `0000ff12-0000-1000-8000-00805f9b34fb`   |
| Lierda 2 | `0000fe60-0000-1000-8000-00805f9b34fb`   |
| Peilin   | `88121427-11e2-52a2-4615-ff00dec16800`   |

## Installation

```bash
pip install desky-ble
```

Requires Python 3.13+.

## Quick start

```python
import asyncio
from bleak import BleakScanner
from desky_ble import DeskyBleClient, DeskState

async def main():
    device = await BleakScanner.find_device_by_name("Desky")

    def on_state(state: DeskState):
        print(f"Height: {state.height_cm} cm, Moving: {state.is_moving}")

    client = DeskyBleClient(device, state_callback=on_state)
    await client.connect()
    await client.request_status()
    await client.move_up()
    await asyncio.sleep(2)
    await client.stop()
    await client.disconnect()

asyncio.run(main())
```

## Features

### Motion control

- `move_up()` / `move_down()` — continuous movement
- `stop()` — stop any movement
- `move_to_height(raw)` — move to a specific height (raw value = cm × 10)

### Memory presets

- `recall_memory(slot)` — recall a saved preset (slots 1–4)
- `save_memory(slot)` — save current height to a preset

### Desk settings

- `set_brightness(value)` — LED display brightness (0–100)
- `set_led_color(value)` — LED colour (1–7)
- `set_lighting(value)` — under-desk lighting (0=off, 1=on)
- `set_vibration(value)` — vibration feedback (0=off, 1=on)
- `set_lock(value)` — child lock (0=off, 1=on)
- `set_anti_collision(value)` — anti-collision sensitivity (1–3)
- `set_touch_mode(value)` — touch mode (0=one-press, 1=hold)
- `set_unit(value)` — display unit
- `set_reminder(minutes)` — sit/stand reminder interval
- `clear_limits()` — clear upper/lower height limits

### State tracking

The `DeskState` object is updated in real-time via BLE notifications:

```python
state = client.state
state.height_cm       # Current height in cm
state.height_raw      # Raw height value
state.is_moving       # Whether the desk is moving
state.lock_status     # Child lock (0=off, 1=on)
state.brightness      # Display brightness (0-100)
state.led_color       # LED colour (1-7)
state.vibration       # Vibration feedback (0=off, 1=on)
state.lighting        # Under-desk lighting (0=off, 1=on)
state.anti_collision  # Anti-collision sensitivity (1-3)
state.has_limits      # Whether height limits are set
```

### Settings persistence

After reconnect, call `restore_settings()` to re-apply any settings that the desk may have reset.

## License

MIT
