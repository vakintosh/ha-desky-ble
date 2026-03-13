from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_MAX_HEIGHT_CM, DEFAULT_MIN_HEIGHT_CM, DOMAIN
from .coordinator import DeskyCoordinator

from desky_ble import height_cm_to_raw


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DeskyCoordinator = hass.data[DOMAIN][entry.entry_id]
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
    _attr_name = "Target Height"
    _attr_icon = "mdi:arrow-expand-vertical"

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_target_height"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }
        self._attr_native_min_value = DEFAULT_MIN_HEIGHT_CM
        self._attr_native_max_value = DEFAULT_MAX_HEIGHT_CM

    @property
    def native_value(self) -> float | None:
        return self.coordinator.desk_state.height_cm

    async def async_set_native_value(self, value: float) -> None:
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
    _attr_name = "Reminder"
    _attr_icon = "mdi:timer-alert"
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_max_value = 120
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_reminder"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    @property
    def native_value(self) -> float | None:

        return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.client.set_reminder(int(value))
