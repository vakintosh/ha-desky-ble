"""Tests for the DeskyBleClient settings command sequence.

Verifies that _send_setting() follows the pattern from the official APK:
  1. Handshake frame  (response=False)
  2. Setting frame #1 (response=True)
  3. Setting frame #2 (response=True)  ← duplicate for reliability
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from custom_components.desky.ble_client import DeskyBleClient
from custom_components.desky.protocol import (
    CMD_HANDSHAKE,
    cmd_set_anti_collision,
    cmd_set_brightness,
    cmd_set_lighting,
    cmd_set_lock,
    cmd_set_vibration,
)


def _make_client() -> DeskyBleClient:
    """Return a DeskyBleClient with a mocked BleakClient already connected."""
    mock_ble_device = MagicMock()
    mock_ble_device.address = "AA:BB:CC:DD:EE:FF"

    client = DeskyBleClient(mock_ble_device)

    # Inject a fake connected BleakClient
    mock_bleak = AsyncMock()
    mock_bleak.is_connected = True
    mock_bleak.write_gatt_char = AsyncMock()
    client._client = mock_bleak  # noqa: SLF001 – needed for unit testing internals
    client._write_char = "fake-char-uuid"  # noqa: SLF001

    return client


@pytest.mark.asyncio
class TestSendSettingSequence:
    """Verify the 3-call sequence: handshake → frame → frame (response=True)."""

    async def _assert_setting_sequence(
        self, client: DeskyBleClient, frame: bytes
    ) -> None:
        """Helper: run _send_setting and assert the exact call order."""
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await client._send_setting(frame)  # noqa: SLF001

        write = client._client.write_gatt_char  # noqa: SLF001
        assert write.call_count == 3, (
            f"Expected 3 write_gatt_char calls, got {write.call_count}"
        )
        expected_calls = [
            call(client._write_char, CMD_HANDSHAKE, response=False),  # noqa: SLF001
            call(client._write_char, frame, response=True),  # noqa: SLF001
            call(client._write_char, frame, response=True),  # noqa: SLF001
        ]
        write.assert_has_calls(expected_calls, any_order=False)

    async def test_set_vibration_on_sequence(self) -> None:
        client = _make_client()
        frame = cmd_set_vibration(1)
        await self._assert_setting_sequence(client, frame)

    async def test_set_vibration_off_sequence(self) -> None:
        client = _make_client()
        frame = cmd_set_vibration(0)
        await self._assert_setting_sequence(client, frame)

    async def test_set_lock_on_sequence(self) -> None:
        client = _make_client()
        frame = cmd_set_lock(1)
        await self._assert_setting_sequence(client, frame)

    async def test_set_lighting_on_sequence(self) -> None:
        client = _make_client()
        frame = cmd_set_lighting(1)
        await self._assert_setting_sequence(client, frame)

    async def test_set_brightness_sequence(self) -> None:
        client = _make_client()
        frame = cmd_set_brightness(80)
        await self._assert_setting_sequence(client, frame)

    async def test_set_anti_collision_sequence(self) -> None:
        client = _make_client()
        frame = cmd_set_anti_collision(2)
        await self._assert_setting_sequence(client, frame)

    async def test_first_write_uses_response_false_for_handshake(self) -> None:
        """The handshake must use response=False (fire-and-forget)."""
        client = _make_client()
        frame = cmd_set_vibration(1)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await client._send_setting(frame)  # noqa: SLF001
        first_call = client._client.write_gatt_char.call_args_list[0]  # noqa: SLF001
        assert first_call == call(client._write_char, CMD_HANDSHAKE, response=False)  # noqa: SLF001

    async def test_setting_writes_use_response_true(self) -> None:
        """Both setting writes must use response=True (GATT Write Request)."""
        client = _make_client()
        frame = cmd_set_vibration(1)
        with patch("asyncio.sleep", new_callable=AsyncMock):
            await client._send_setting(frame)  # noqa: SLF001
        calls = client._client.write_gatt_char.call_args_list  # noqa: SLF001
        for idx in (1, 2):
            kwargs = calls[idx][1]  # keyword args
            assert kwargs.get("response") is True, (
                f"Write #{idx} must use response=True"
            )

    async def test_disconnected_raises(self) -> None:
        """Should raise RuntimeError if not connected when calling _send_setting."""
        client = _make_client()
        client._client = None  # noqa: SLF001
        frame = cmd_set_vibration(1)
        with pytest.raises(RuntimeError, match="Not connected"):
            await client._send_setting(frame)  # noqa: SLF001
