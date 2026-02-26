"""Tests for DeskyBleClient.restore_settings().

Verifies that user-set settings (eg vibration=ON) are persisted in
_desired_settings and correctly re-applied after a reconnect cycle
restores the desk to its EEPROM defaults.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.desky.ble_client import DeskyBleClient
from custom_components.desky.protocol import (
    cmd_set_brightness,
    cmd_set_lighting,
    cmd_set_vibration,
)


def _make_client() -> DeskyBleClient:
    """Return a DeskyBleClient with a mocked BleakClient already connected."""
    mock_ble_device = MagicMock()
    mock_ble_device.address = "AA:BB:CC:DD:EE:FF"

    client = DeskyBleClient(mock_ble_device)

    mock_bleak = AsyncMock()
    mock_bleak.is_connected = True
    mock_bleak.write_gatt_char = AsyncMock()
    client._client = mock_bleak  # noqa: SLF001
    client._write_char = "fake-char-uuid"  # noqa: SLF001

    return client


@pytest.mark.asyncio
class TestRestoreSettings:
    """Verify that restore_settings() re-applies user-set values after reconnect."""

    async def test_restore_sends_desired_frame_when_desk_differs(self) -> None:
        """After set_vibration(1), if desk reports vibration=0, frame is re-sent."""
        client = _make_client()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await client.set_vibration(1)

        # Simulate desk reverting to EEPROM default after reconnect
        client._state.vibration = 0  # noqa: SLF001

        # Reset mock so we only count restore_settings writes
        client._client.write_gatt_char.reset_mock()  # noqa: SLF001

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await client.restore_settings()

        # Should have written the 3-call sequence: handshake + 2× frame
        assert client._client.write_gatt_char.call_count == 3  # noqa: SLF001

    async def test_restore_skips_when_desk_already_matches(self) -> None:
        """If desk already reports the desired value, no extra writes are sent."""
        client = _make_client()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await client.set_vibration(1)

        # Desk already matches the desired value
        client._state.vibration = 1  # noqa: SLF001
        client._client.write_gatt_char.reset_mock()  # noqa: SLF001

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await client.restore_settings()

        # No writes should happen
        client._client.write_gatt_char.assert_not_called()

    async def test_restore_multiple_settings(self) -> None:
        """Multiple dirty settings (vibration + lighting) are all re-applied."""
        client = _make_client()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await client.set_vibration(1)
            await client.set_lighting(1)

        # Desk reverts both to 0
        client._state.vibration = 0  # noqa: SLF001
        client._state.lighting = 0  # noqa: SLF001
        client._client.write_gatt_char.reset_mock()  # noqa: SLF001

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await client.restore_settings()

        # Two settings × 3 calls each = 6 total
        assert client._client.write_gatt_char.call_count == 6  # noqa: SLF001

    async def test_set_methods_record_desired(self) -> None:
        """Each set_* call must populate _desired_settings with the correct value."""
        client = _make_client()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await client.set_vibration(1)
            await client.set_lighting(0)
            await client.set_brightness(75)

        ds = client._desired_settings  # noqa: SLF001
        assert ds["vibration"] == (1, cmd_set_vibration(1))
        assert ds["lighting"] == (0, cmd_set_lighting(0))
        assert ds["brightness"] == (75, cmd_set_brightness(75))

    async def test_restore_empty_when_no_settings_set(self) -> None:
        """If no set_* was ever called, restore_settings() is a no-op."""
        client = _make_client()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await client.restore_settings()

        client._client.write_gatt_char.assert_not_called()  # noqa: SLF001

    async def test_set_vibration_overwrites_previous_desired(self) -> None:
        """Calling set_vibration() twice keeps only the most recent desired value."""
        client = _make_client()

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await client.set_vibration(1)
            await client.set_vibration(0)

        desired_value, _ = client._desired_settings["vibration"]  # noqa: SLF001
        assert desired_value == 0
