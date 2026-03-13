# Home Assistant Desky BLE Controller
A custom integration for Home Assistant that enables control of Desky-compatible standing desks via Bluetooth Low Energy (BLE). This project allows for the integration of physical workspace hardware into home automation environments.

## Disclaimer
This project is an independent community contribution and is not affiliated with, authorized, or endorsed by Desky®. It was created out of a genuine appreciation for the product and a desire to integrate it into a smart home environment.

This integration communicates with your desk over local Bluetooth only — it does not bypass any cloud security, access any online services, or modify desk firmware. Use this software at your own risk; the author is not responsible for any damage to hardware, property, or personal injury resulting from its use.

Interoperability research was conducted in accordance with Canada's *Copyright Act* (Section 30.6), which permits reverse engineering for the purpose of achieving interoperability between independently created programs.

## Features
- **Height Control**: Set and adjust desk height directly from Home Assistant.
- **Presets**: Trigger existing desk memory positions.
- **Real-time Monitoring**: View current desk height and connection status.
- **Local Control**: Operates entirely over local BLE without the need for external cloud APIs.

## Compatible Hardware
This integration requires the **Desky Bluetooth Controller**. Other controllers or desk brands are not supported.

## Prerequisites
- A Home Assistant instance with a functional Bluetooth adapter or an ESPHome Bluetooth Proxy.
- A Desky standing desk equipped with the Bluetooth Controller.
- Python 3.9+ (if running standalone scripts).

## Tested On
This integration has been tested with the following Home Assistant environment:
- **Installation method**: Home Assistant OS
- **Core**: 2026.2.1
- **Supervisor**: 2026.02.2
- **Operating System**: 17.0
- **Frontend**: 20260128.6

## Entities
Once configured, the integration creates the following entities for your desk:

| Entity | Type | Description |
|--------|------|-------------|
| Height | Sensor | Current desk height in cm or inches |
| Desk | Cover | Open (up) / Close (down) / Stop / Set position |
| Target Height | Number | Move to a specific height (slider) |
| Reminder | Number | Inactivity reminder timer (0–120 min) |
| Preset 1–4 | Button | Recall a saved memory position |
| Save Preset 1–4 | Button | Save the current height to a preset slot (disabled by default) |
| LED Color | Select | Set LED strip color |
| Anti-Collision Sensitivity | Select | High / Medium / Low |
| Touch Mode | Select | One Press / Press and Hold |
| Child Lock | Switch | Enable or disable the physical controls |
| Vibration | Switch | Toggle vibration feedback |
| LED Lighting | Switch | Toggle the LED strip on/off |

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

## Protocol Documentation
The implementation is based on the following BLE characteristics identified during the reverse engineering process (note that UUIDs vary depending on the specific controller variant):

### Lierda Variant 1
- **Service UUID:** `0000ff12-0000-1000-8000-00805f9b34fb`
- **Command Characteristic:** `0000ff01-0000-1000-8000-00805f9b34fb`
- **Notify Characteristic:** `0000ff02-0000-1000-8000-00805f9b34fb`

### Lierda Variant 2
- **Service UUID:** `0000fe60-0000-1000-8000-00805f9b34fb`
- **Command Characteristic:** `0000fe61-0000-1000-8000-00805f9b34fb`
- **Notify Characteristic:** `0000fe62-0000-1000-8000-00805f9b34fb`

### Peilin Variant
- **Service UUID:** `88121427-11e2-52a2-4615-ff00dec16800`
- **Command / Notify Characteristic:** `88121427-11e2-52a2-4615-ff00dec16801`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Desk not found during setup | Ensure the desk is powered on and the Bluetooth controller LED is blinking. Move the HA host or ESPHome Bluetooth proxy closer to the desk. |
| Frequent disconnects | BLE range is limited (~10 m). An ESPHome Bluetooth proxy placed near the desk significantly improves reliability. |
| Entities show *Unavailable* | The integration will automatically reconnect on the next poll cycle (default: 30 s). Check **Settings → System → Logs** for BLE errors. |
| Presets not saving | Press the *Save Preset* button (disabled by default — enable it first in the entity settings). |
| Settings reset after reconnect | This is expected BLE behavior — the integration automatically restores your preferred settings after each reconnect. |

## License
This project is licensed under the MIT License. See the `LICENSE` file for details. This license includes a standard limitation of liability clause.
