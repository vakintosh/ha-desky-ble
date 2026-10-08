"""Tests for DeskyCoordinator advertisement-driven reconnect + backoff.

Covers the behavior added on top of the DataUpdateCoordinator poll loop:
- bluetooth.async_register_callback / async_track_unavailable wiring
- immediate reconnect attempt on advertisement when disconnected
- exponential backoff (5s -> 120s cap) on repeated failed reconnects,
  reset to the minimum on first success
- the poll loop (_async_update_data) never attempts a connect itself
- clean shutdown: cancel pending timers/tasks, unregister listeners
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.desky.const import (
    RECONNECT_BACKOFF_MAX_SECONDS,
    RECONNECT_BACKOFF_MIN_SECONDS,
)
from custom_components.desky.coordinator import DeskyCoordinator
from desky_ble import DeskState


def _make_ble_device(address: str = "AA:BB:CC:DD:EE:FF") -> MagicMock:
    device = MagicMock()
    device.address = address
    return device


def _make_entry() -> MagicMock:
    entry = MagicMock()

    def _create_background_task(
        _hass: object, coro: object, name: object
    ) -> asyncio.Task:
        return asyncio.ensure_future(coro)

    entry.async_create_background_task.side_effect = _create_background_task
    return entry


@pytest.fixture
def hass() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    client.is_connected = False
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.request_all_settings = AsyncMock()
    client.restore_settings = AsyncMock()
    client.request_status = AsyncMock()
    client.set_ble_device = MagicMock()
    client.state = DeskState()
    return client


@pytest.fixture
def coordinator(hass: MagicMock, mock_client: MagicMock) -> DeskyCoordinator:
    ble_device = _make_ble_device()
    entry = _make_entry()
    with patch(
        "custom_components.desky.coordinator.DeskyBleClient", return_value=mock_client
    ):
        coord = DeskyCoordinator(hass, entry, ble_device)
    return coord


@pytest.fixture
def bt_mocks():
    with (
        patch("custom_components.desky.coordinator.async_register_callback") as reg,
        patch("custom_components.desky.coordinator.async_track_unavailable") as unavail,
        patch("custom_components.desky.coordinator.async_call_later") as call_later,
    ):
        reg.return_value = MagicMock(name="unsub_advertisement")
        unavail.return_value = MagicMock(name="unsub_unavailable")
        call_later.return_value = MagicMock(name="unsub_backoff")
        yield {"register": reg, "unavailable": unavail, "call_later": call_later}


# ---------------------------------------------------------------------------
# async_setup() registers bluetooth listeners
# ---------------------------------------------------------------------------


def test_async_setup_registers_advertisement_and_unavailable_callbacks(
    coordinator: DeskyCoordinator, bt_mocks: dict
) -> None:
    coordinator.async_setup()

    bt_mocks["register"].assert_called_once()
    bt_mocks["unavailable"].assert_called_once()


# ---------------------------------------------------------------------------
# Advertisement handling
# ---------------------------------------------------------------------------


def test_advertisement_triggers_immediate_reconnect_when_disconnected(
    coordinator: DeskyCoordinator, mock_client: MagicMock, bt_mocks: dict
) -> None:
    mock_client.is_connected = False
    service_info = MagicMock()
    service_info.device = _make_ble_device()

    coordinator._async_handle_advertisement(service_info, MagicMock())

    mock_client.set_ble_device.assert_called_once_with(service_info.device)
    bt_mocks["call_later"].assert_called_once()
    (_hass, delay, _cb), _kwargs = bt_mocks["call_later"].call_args
    assert delay == 0


def test_advertisement_updates_device_but_skips_reconnect_when_connected(
    coordinator: DeskyCoordinator, mock_client: MagicMock, bt_mocks: dict
) -> None:
    mock_client.is_connected = True
    service_info = MagicMock()
    service_info.device = _make_ble_device()

    coordinator._async_handle_advertisement(service_info, MagicMock())

    mock_client.set_ble_device.assert_called_once_with(service_info.device)
    bt_mocks["call_later"].assert_not_called()


# ---------------------------------------------------------------------------
# Unavailable handling
# ---------------------------------------------------------------------------


def test_unavailable_cancels_pending_backoff_and_marks_update_error(
    coordinator: DeskyCoordinator, bt_mocks: dict
) -> None:
    pending_unsub = MagicMock()
    coordinator._unsub_backoff = pending_unsub

    coordinator._async_handle_unavailable(MagicMock())

    pending_unsub.assert_called_once()
    assert coordinator._unsub_backoff is None
    assert coordinator.last_update_success is False


# ---------------------------------------------------------------------------
# Backoff scheduling across repeated failures
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_backoff_doubles_on_repeated_failures_and_caps_at_max(
    coordinator: DeskyCoordinator, mock_client: MagicMock, bt_mocks: dict
) -> None:
    mock_client.connect.side_effect = RuntimeError("out of range")

    expected_delays = []
    delay = RECONNECT_BACKOFF_MIN_SECONDS
    for _ in range(6):
        expected_delays.append(min(delay, RECONNECT_BACKOFF_MAX_SECONDS))
        delay *= 2

    for expected_delay in expected_delays:
        coordinator._async_reconnect_attempt(None)
        await coordinator._reconnect_task
        last_call = bt_mocks["call_later"].call_args
        (_hass, scheduled_delay, _cb), _kwargs = last_call
        assert scheduled_delay == expected_delay


@pytest.mark.asyncio
async def test_successful_reconnect_resets_backoff_and_pushes_state(
    coordinator: DeskyCoordinator, mock_client: MagicMock, bt_mocks: dict
) -> None:
    mock_client.connect.side_effect = [RuntimeError("fail"), None]

    coordinator._async_reconnect_attempt(None)
    await coordinator._reconnect_task
    assert coordinator._failed_attempts == 1

    bt_mocks["call_later"].reset_mock()
    coordinator._async_reconnect_attempt(None)
    await coordinator._reconnect_task

    assert coordinator._failed_attempts == 0
    assert coordinator.data is mock_client.state
    bt_mocks["call_later"].assert_not_called()


# ---------------------------------------------------------------------------
# Poll loop never connects
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_poll_loop_raises_without_connecting_when_disconnected(
    coordinator: DeskyCoordinator, mock_client: MagicMock
) -> None:
    mock_client.is_connected = False

    with pytest.raises(Exception, match="not connected"):
        await coordinator._async_update_data()

    mock_client.connect.assert_not_called()


@pytest.mark.asyncio
async def test_poll_loop_polls_status_when_connected(
    coordinator: DeskyCoordinator, mock_client: MagicMock
) -> None:
    mock_client.is_connected = True

    with patch("custom_components.desky.coordinator.asyncio.sleep", new=AsyncMock()):
        result = await coordinator._async_update_data()

    mock_client.request_status.assert_awaited_once()
    mock_client.connect.assert_not_called()
    assert result is mock_client.state


# ---------------------------------------------------------------------------
# Initial connect (used by __init__.py before first refresh)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_connect_performs_connect_sequence(
    coordinator: DeskyCoordinator, mock_client: MagicMock
) -> None:
    with patch("custom_components.desky.coordinator.asyncio.sleep", new=AsyncMock()):
        await coordinator.async_connect()

    mock_client.connect.assert_awaited_once()
    mock_client.request_all_settings.assert_awaited_once()
    mock_client.restore_settings.assert_awaited_once()


# ---------------------------------------------------------------------------
# Shutdown cleans everything up
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_shutdown_cancels_timers_and_unregisters_listeners(
    coordinator: DeskyCoordinator, mock_client: MagicMock, bt_mocks: dict
) -> None:
    coordinator.async_setup()
    backoff_unsub = MagicMock()
    coordinator._unsub_backoff = backoff_unsub

    await coordinator.async_shutdown()

    backoff_unsub.assert_called_once()
    bt_mocks["register"].return_value.assert_called_once()
    bt_mocks["unavailable"].return_value.assert_called_once()
    mock_client.disconnect.assert_awaited_once()
