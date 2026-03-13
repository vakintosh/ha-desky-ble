# Home Assistant Desky BLE Controller
A custom integration for Home Assistant that enables control of Desky-compatible standing desks via Bluetooth Low Energy (BLE). This project allows for the integration of physical workspace hardware into home automation environments.

## Disclaimer
This project is not affiliated with, endorsed by, or supported by Desky.

The information and code provided in this repository are for educational and interoperability purposes only. Use this software at your own risk. The author is not responsible for any damage to hardware, property, or personal injury resulting from the use of this code.

Reverse engineering was performed solely for the purpose of achieving interoperability between the desk hardware and the Home Assistant ecosystem, as permitted under relevant copyright provisions for non-commercial use.

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

Specific byte sequences for height adjustment and memory presets are documented in the `/docs` folder of this repository.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details. This license includes a standard limitation of liability clause.
