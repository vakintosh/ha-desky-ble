"""Tests for custom_components.desky.__init__ setup/unload flow.

Covers the wiring added for advertisement-driven reconnect: the coordinator
is constructed with the ConfigEntry, has its bluetooth listeners registered
via async_setup(), performs the one-time initial connect via async_connect()
before the first refresh, and a failed initial connect surfaces as
ConfigEntryNotReady.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.desky import async_setup_entry, async_unload_entry


def _make_entry(address: str = "AA:BB:CC:DD:EE:FF") -> MagicMock:
    entry = MagicMock()
    entry.data = {"address": address}
    entry.options = {}
    entry.runtime_data = None
    return entry


@pytest.mark.asyncio
async def test_async_setup_entry_connects_before_first_refresh() -> None:
    hass = MagicMock()
    entry = _make_entry()

    mock_coordinator = MagicMock()
    mock_coordinator.async_setup = MagicMock()
    mock_coordinator.async_connect = AsyncMock()
    mock_coordinator.async_config_entry_first_refresh = AsyncMock()
    hass.config_entries.async_forward_entry_setups = AsyncMock()

    with (
        patch(
            "custom_components.desky.async_ble_device_from_address",
            return_value=MagicMock(),
        ),
        patch(
            "custom_components.desky.DeskyCoordinator", return_value=mock_coordinator
        ),
    ):
        result = await async_setup_entry(hass, entry)

    assert result is True
    mock_coordinator.async_setup.assert_called_once()
    mock_coordinator.async_connect.assert_awaited_once()
    mock_coordinator.async_config_entry_first_refresh.assert_awaited_once()
    # Connect must happen before the first refresh (order matters).
    assert mock_coordinator.mock_calls.index(
        ("async_connect", (), {})
    ) < mock_coordinator.mock_calls.index(("async_config_entry_first_refresh", (), {}))
    assert entry.runtime_data is mock_coordinator


@pytest.mark.asyncio
async def test_async_setup_entry_raises_not_ready_on_connect_failure() -> None:
    from homeassistant.exceptions import ConfigEntryNotReady

    hass = MagicMock()
    entry = _make_entry()

    mock_coordinator = MagicMock()
    mock_coordinator.async_setup = MagicMock()
    mock_coordinator.async_connect = AsyncMock(side_effect=RuntimeError("out of range"))

    with (
        patch(
            "custom_components.desky.async_ble_device_from_address",
            return_value=MagicMock(),
        ),
        patch(
            "custom_components.desky.DeskyCoordinator", return_value=mock_coordinator
        ),
        pytest.raises(ConfigEntryNotReady),
    ):
        await async_setup_entry(hass, entry)


@pytest.mark.asyncio
async def test_async_unload_entry_calls_coordinator_shutdown() -> None:
    hass = MagicMock()
    entry = _make_entry()
    entry.runtime_data = MagicMock()
    entry.runtime_data.async_shutdown = AsyncMock()
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    result = await async_unload_entry(hass, entry)

    assert result is True
    entry.runtime_data.async_shutdown.assert_awaited_once()
