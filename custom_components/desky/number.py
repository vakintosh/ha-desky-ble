"""Support for Desky BLE standing desk number platform."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import CONF_ADDRESS, UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DeskyConfigEntry
from .const import DEFAULT_MAX_HEIGHT_CM, DEFAULT_MIN_HEIGHT_CM, DOMAIN
from .coordinator import DeskyCoordinator

from desky_ble import height_cm_to_raw

_LOGGER = logging.getLogger(__name__)

DEBOUNCE_SECONDS = 0.5


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DeskyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Desky number platform."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            DeskyTargetHeight(coordinator, entry),
            DeskyReminder(coordinator, entry),
        ]
    )


class DeskyTargetHeight(CoordinatorEntity[DeskyCoordinator], NumberEntity):
    """Number entity for setting an exact target height in cm."""

    _attr_device_class = NumberDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.CENTIMETERS
    _attr_mode = NumberMode.SLIDER
    _attr_native_step = 0.1
    _attr_has_entity_name = True
    _attr_translation_key = "target_height"

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{address}_target_height"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
        )
        self._attr_native_min_value = DEFAULT_MIN_HEIGHT_CM
        self._attr_native_max_value = DEFAULT_MAX_HEIGHT_CM
        self._debounce_handle: asyncio.TimerHandle | None = None

    @property
    def native_value(self) -> float | None:
        return self.coordinator.desk_state.height_cm

    async def async_set_native_value(self, value: float) -> None:
        if self._debounce_handle is not None:
            self._debounce_handle.cancel()
        loop = asyncio.get_running_loop()
        self._debounce_handle = loop.call_later(
            DEBOUNCE_SECONDS,
            lambda: asyncio.ensure_future(self._send_height(value)),
        )

    async def _send_height(self, value: float) -> None:
        """Actually send the height command after debounce."""
        raw = height_cm_to_raw(value)
        await self.coordinator.client.move_to_height(raw)


class DeskyReminder(CoordinatorEntity[DeskyCoordinator], NumberEntity):
    """Number entity for the desk's built-in reminder / alert timer.

    The desk controller has an internal countdown (opcode 0xB1 SET_REMINDER).
    When set to N minutes the controller buzzes once when the timer expires.
    Setting the value to 0 disables any active reminder.

    Use this as a pre-alert buzzer from automations:
        1. Set reminder to 1 (or 2) minutes before a posture change.
        2. When the desk buzzes, the posture-change automation fires.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "reminder"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 120
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{address}_reminder"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
        )

    @property
    def native_value(self) -> float | None:

        return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.client.set_reminder(int(value))
