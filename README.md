# Home Assistant Desky BLE Controller
A custom integration for Home Assistant that enables control of Desky-compatible standing desks via Bluetooth Low Energy (BLE). This project allows for the integration of physical workspace hardware into home automation environments.

## Disclaimer
This project is an independent community contribution and is not affiliated with, authorized, or endorsed by Desky®. It was created out of a genuine appreciation for the product and a desire to integrate it into a smart home environment.

This integration communicates with your desk over local Bluetooth only , it does not bypass any cloud security, access any online services, or modify desk firmware. Use this software at your own risk; the author is not responsible for any damage to hardware, property, or personal injury resulting from its use.

Interoperability research was conducted in accordance with Canada's *Copyright Act* (Section 30.6), which permits reverse engineering for the purpose of achieving interoperability between independently created programs.

## Features
- **Height Control**: Set and adjust desk height directly from Home Assistant.
- **Presets**: Trigger and save desk memory positions (4 slots).
- **Real-time Monitoring**: View current desk height and connection status.
- **Settings Control**: LED color, anti-collision sensitivity, touch mode, child lock, vibration, and LED lighting.
- **Settings Persistence**: User-configured settings are automatically restored after BLE reconnects.
- **Local Control**: Operates entirely over local BLE — no cloud APIs or internet required.
- **Translatable UI**: Entity names and select options use Home Assistant's translation framework.
- **Reconfigure & Re-auth**: Update the BLE address post-setup without removing the device.

## Compatible Hardware
This integration requires the **Desky Bluetooth Controller**. Other controllers or desk brands are not supported.

## Prerequisites
- Home Assistant 2026.2+ with Python 3.13.2+.
- A functional Bluetooth adapter or an ESPHome Bluetooth Proxy.
- A Desky standing desk equipped with the Bluetooth Controller.

## Tested On
This integration has been tested with the following Home Assistant environment:
- **Installation method**: Home Assistant OS
- **Core**: 2026.2.1
- **Supervisor**: 2026.02.2
- **Operating System**: 17.0
- **Frontend**: 20260128.6

## Entities
Once configured, the integration creates the following entities for your desk:

| Entity | Type | Category | Description |
|--------|------|----------|-------------|
| Desk | Cover | Controls | Open (up) / Close (down) / Stop / Set position |
| Target Height | Number | Controls | Move to a specific height via slider (debounced) |
| Preset 1–4 | Button | Controls | Recall a saved memory position |
| Save Preset 1–4 | Button | Controls | Save current height to a preset slot (disabled by default) |
| Height | Sensor | Sensors | Current desk height in cm or inches |
| Reminder | Number | Configuration | Inactivity reminder timer (0–120 min) |
| LED Color | Select | Configuration | Set LED strip color (debounced) |
| Anti-Collision Sensitivity | Select | Configuration | High / Medium / Low (debounced) |
| Touch Mode | Select | Configuration | One Press / Press and Hold (debounced) |
| Child Lock | Switch | Configuration | Enable or disable the physical controls |
| Vibration | Switch | Configuration | Toggle vibration feedback |
| LED Lighting | Switch | Configuration | Toggle the LED strip on/off |

## Architecture
The BLE protocol layer (frame encoding, command opcodes, notification parsing, and connection management) lives in a separate [`desky-ble`](https://pypi.org/project/desky-ble/) Python package. The Home Assistant integration imports it as a runtime dependency — this keeps the integration focused on HA platform glue and makes the BLE logic reusable outside HA.

## Installation
### Manual Installation
1. Download the `custom_components/desky` folder from this repository.
2. Copy the folder into your Home Assistant `config/custom_components/` directory.
3. Restart Home Assistant.

## Configuration
Once the integration is installed:

1. Go to **Settings > Devices & Services**.
2. Click **Add Integration**.
3. Search for **Desky BLE**.
4. Follow the on-screen prompts to pair with your desk.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Desk not found during setup | Ensure the desk is powered on and the Bluetooth controller LED is blinking. Move the HA host or ESPHome Bluetooth proxy closer to the desk. |
| Frequent disconnects | BLE range is limited (~10 m). An ESPHome Bluetooth proxy placed near the desk significantly improves reliability. |
| Entities show *Unavailable* | The integration will automatically reconnect on the next poll cycle (default: 30 s). Check **Settings → System → Logs** for BLE errors. |
| Presets not saving | Press the *Save Preset* button (disabled by default — enable it first in the entity settings). |
| Settings reset after reconnect | This is expected BLE behavior — the integration automatically restores your preferred settings after each reconnect. |
| BLE address changed | Use **Settings → Devices & Services → Desky → Configure → Reconfigure** to update the address without re-adding the device. |

## License
This project is licensed under the MIT License. See the `LICENSE` file for details. This license includes a standard limitation of liability clause.
