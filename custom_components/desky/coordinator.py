"""Desky data-update coordinator.

Manages the BLE client lifecycle and distributes desk state to all entities.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ble_client import DeskyBleClient
from .const import DEFAULT_POLL_INTERVAL, DOMAIN
from .protocol import DeskState

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice

_LOGGER = logging.getLogger(__name__)


class DeskyCoordinator(DataUpdateCoordinator[DeskState]):
    """Coordinator that owns the BLE connection and polls for status."""

    def __init__(
        self,
        hass: HomeAssistant,
        ble_device: BLEDevice,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )
        self._ble_device = ble_device
        self._client = DeskyBleClient(
            ble_device,
            state_callback=self._on_state_update,
        )

    @property
    def client(self) -> DeskyBleClient:
        return self._client

    @property
    def desk_state(self) -> DeskState:
        return self._client.state

    # ------------------------------------------------------------------
    # State push (from BLE notifications → entity updates)
    # ------------------------------------------------------------------
    @callback
    def _on_state_update(self, _state: DeskState) -> None:
        """Called by the BLE client whenever a notification is parsed."""
        self.async_set_updated_data(self._client.state)

    # ------------------------------------------------------------------
    # Polling (DataUpdateCoordinator interface)
    # ------------------------------------------------------------------
    async def _async_update_data(self) -> DeskState:
        """Connect (if needed) and poll the desk for status."""
        try:
            if not self._client.is_connected:
                await self._client.connect()
                # After reconnect, fetch all settings once
                await self._client.request_all_settings()

            await self._client.request_status()
            # Small delay so notifications can arrive before we return
            await asyncio.sleep(0.5)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with desk: {err}") from err
        return self._client.state

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    async def async_shutdown(self) -> None:
        """Disconnect BLE client on HA shutdown."""
        await self._client.disconnect()
