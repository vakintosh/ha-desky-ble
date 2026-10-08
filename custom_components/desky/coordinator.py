"""DataUpdateCoordinator for Desky BLE standing desks."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothScanningMode,
    async_register_callback,
    async_track_unavailable,
)
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from desky_ble import DeskState, DeskyBleClient

from .const import (
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    RECONNECT_BACKOFF_MAX_SECONDS,
    RECONNECT_BACKOFF_MIN_SECONDS,
)

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import CALLBACK_TYPE

_LOGGER = logging.getLogger(__name__)


class DeskyCoordinator(DataUpdateCoordinator[DeskState]):
    """Coordinator that owns the BLE connection and polls for status.

    Reconnects are *not* driven by the poll loop. Instead:
    - `async_register_callback` fires on every advertisement seen for this
      address, triggering an immediate reconnect attempt when disconnected.
    - `async_track_unavailable` fires when the Bluetooth stack stops hearing
      the device at all, cancelling any pending retry and marking the
      coordinator's data as errored.
    - Failed reconnect attempts self-schedule the next attempt with
      exponential backoff (`RECONNECT_BACKOFF_MIN/MAX_SECONDS`), reset to the
      minimum on the first successful reconnect.

    The poll loop (`_async_update_data`) only ever polls status on an
    already-connected client; it never attempts to connect itself.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        ble_device: BLEDevice,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )
        self._entry = entry
        self._ble_device = ble_device
        self._client = DeskyBleClient(
            ble_device,
            state_callback=self._on_state_update,
        )
        self._failed_attempts = 0
        self._unsub_advertisement: CALLBACK_TYPE | None = None
        self._unsub_unavailable: CALLBACK_TYPE | None = None
        self._unsub_stop: CALLBACK_TYPE | None = None
        self._unsub_backoff: CALLBACK_TYPE | None = None
        self._reconnect_task: asyncio.Task[None] | None = None

    @property
    def client(self) -> DeskyBleClient:
        return self._client

    @property
    def desk_state(self) -> DeskState:
        return self._client.state

    @callback
    def _on_state_update(self, _state: DeskState) -> None:
        """Called by the BLE client whenever a notification is parsed."""
        self.async_set_updated_data(self._client.state)

    @callback
    def async_setup(self) -> None:
        """Register bluetooth listeners for advertisement-driven reconnect."""
        address = self._ble_device.address
        self._unsub_advertisement = async_register_callback(
            self.hass,
            self._async_handle_advertisement,
            BluetoothCallbackMatcher(address=address),
            BluetoothScanningMode.PASSIVE,
        )
        self._unsub_unavailable = async_track_unavailable(
            self.hass,
            self._async_handle_unavailable,
            address,
            connectable=True,
        )
        self._unsub_stop = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, self._async_handle_stop
        )

    @callback
    def _async_handle_advertisement(
        self, service_info: object, _change: object
    ) -> None:
        """An advertisement was seen for our address.

        Rebind to the (possibly fresher) BLEDevice and, if disconnected,
        attempt a reconnect immediately rather than waiting on backoff.
        """
        self._client.set_ble_device(service_info.device)  # type: ignore[attr-defined]
        if self._client.is_connected:
            return
        self._async_schedule_reconnect(0)

    @callback
    def _async_handle_unavailable(self, _service_info: object) -> None:
        """The bluetooth stack stopped hearing the desk entirely."""
        self._cancel_backoff()
        self.async_set_update_error(UpdateFailed("Desk is no longer in range"))

    @callback
    def _async_handle_stop(self, _event: object) -> None:
        """HA is shutting down; don't let a scheduled retry fire mid-stop."""
        self._cancel_backoff()

    @callback
    def _cancel_backoff(self) -> None:
        if self._unsub_backoff is not None:
            self._unsub_backoff()
            self._unsub_backoff = None

    @callback
    def _async_schedule_reconnect(self, delay: float) -> None:
        self._cancel_backoff()
        self._unsub_backoff = async_call_later(
            self.hass, delay, self._async_reconnect_attempt
        )

    @callback
    def _async_reconnect_attempt(self, _now: object) -> None:
        self._unsub_backoff = None
        if self._client.is_connected:
            return
        if self._reconnect_task is not None and not self._reconnect_task.done():
            return
        self._reconnect_task = self._entry.async_create_background_task(
            self.hass,
            self._async_do_reconnect(),
            name=f"{DOMAIN}_reconnect",
        )

    async def _async_perform_connect(self) -> None:
        await self._client.connect()
        await self._client.request_all_settings()
        await asyncio.sleep(0.6)
        await self._client.restore_settings()

    async def _async_do_reconnect(self) -> None:
        try:
            await self._async_perform_connect()
        except Exception:
            _LOGGER.debug("Reconnect attempt failed", exc_info=True)
            self._failed_attempts += 1
            delay = min(
                RECONNECT_BACKOFF_MIN_SECONDS * (2 ** (self._failed_attempts - 1)),
                RECONNECT_BACKOFF_MAX_SECONDS,
            )
            self._async_schedule_reconnect(delay)
        else:
            self._failed_attempts = 0
            self.async_set_updated_data(self._client.state)

    async def async_connect(self) -> None:
        """Perform the initial connection (called once during entry setup)."""
        await self._async_perform_connect()

    async def _async_update_data(self) -> DeskState:
        """Poll the desk for status. Never attempts to (re)connect."""
        if not self._client.is_connected:
            raise UpdateFailed("Desk is not connected")
        try:
            await self._client.request_status()
            await asyncio.sleep(0.5)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with desk: {err}") from err
        return self._client.state

    async def async_shutdown(self) -> None:
        """Cancel pending timers/tasks, unregister listeners, disconnect."""
        self._cancel_backoff()
        if self._reconnect_task is not None and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        for unsub in (
            self._unsub_advertisement,
            self._unsub_unavailable,
            self._unsub_stop,
        ):
            if unsub is not None:
                unsub()
        self._unsub_advertisement = None
        self._unsub_unavailable = None
        self._unsub_stop = None
        await self._client.disconnect()
