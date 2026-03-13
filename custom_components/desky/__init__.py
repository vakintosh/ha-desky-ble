"""Support for Desky BLE standing desks."""

from __future__ import annotations

import logging

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
from .coordinator import DeskyCoordinator

_LOGGER = logging.getLogger(__name__)

type DeskyConfigEntry = ConfigEntry[DeskyCoordinator]

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.COVER,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: DeskyConfigEntry) -> bool:
    """Set up Desky from a config entry."""
    address: str = entry.data[CONF_ADDRESS]
    poll_interval: int = entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)

    ble_device = async_ble_device_from_address(hass, address, connectable=True)
    if ble_device is None:
        raise ConfigEntryNotReady(
            f"Could not find Desky BLE device with address {address}"
        )

    coordinator = DeskyCoordinator(hass, ble_device, poll_interval)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: DeskyConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        await entry.runtime_data.async_shutdown()
    return unload_ok


async def _async_update_options(
    hass: HomeAssistant, entry: DeskyConfigEntry
) -> None:
    """Handle options update by reloading the entry."""
    await hass.config_entries.async_reload(entry.entry_id)
