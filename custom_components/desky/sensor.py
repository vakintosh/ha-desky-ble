"""Desky height sensor platform."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DeskyCoordinator
from .protocol import height_is_cm


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DeskyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DeskyHeightSensor(coordinator, entry)])


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
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_height"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

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
