"""Support for Desky BLE standing desk sensor platform."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_ADDRESS, UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DeskyConfigEntry
from .const import DOMAIN
from .coordinator import DeskyCoordinator

from desky_ble import height_is_cm


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DeskyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Desky sensor platform."""
    async_add_entities([DeskyHeightSensor(entry.runtime_data, entry)])


class DeskyHeightSensor(CoordinatorEntity[DeskyCoordinator], SensorEntity):
    """Reports the current desk height."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_has_entity_name = True
    _attr_name = "Height"
    _attr_icon = "mdi:human-male-height-variant"

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{address}_height"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
        )

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.desk_state.height_raw
        if raw is None:
            return None
        return raw / 10.0

    @property
    def native_unit_of_measurement(self) -> str:
        raw = self.coordinator.desk_state.height_raw
        if raw is not None and not height_is_cm(raw):
            return UnitOfLength.INCHES
        return UnitOfLength.CENTIMETERS
