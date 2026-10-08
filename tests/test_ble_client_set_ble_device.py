"""Tests for DeskyBleClient.set_ble_device().

Needed for advertisement-driven reconnect: when the desk is heard via a
different Bluetooth proxy/adapter, the coordinator rebinds the client to the
fresher BLEDevice before the next connect attempt.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from desky_ble import DeskyBleClient


def test_set_ble_device_updates_target_without_touching_connection() -> None:
    original_device = MagicMock()
    original_device.address = "AA:BB:CC:DD:EE:FF"

    client = DeskyBleClient(original_device)

    fake_bleak_client = MagicMock()
    fake_bleak_client.is_connected = True
    client._client = fake_bleak_client

    new_device = MagicMock()
    new_device.address = "AA:BB:CC:DD:EE:FF"

    client.set_ble_device(new_device)

    assert client._ble_device is new_device
    # Existing connection state untouched by a device rebind.
    assert client.is_connected is True
