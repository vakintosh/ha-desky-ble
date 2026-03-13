from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DeskyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DeskyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            DeskyChildLockSwitch(coordinator, entry),
            DeskyVibrationSwitch(coordinator, entry),
            DeskyLightingSwitch(coordinator, entry),
        ]
    )


class _DeskySwitch(CoordinatorEntity[DeskyCoordinator], SwitchEntity):
    """Base for Desky toggle switches."""

    _attr_has_entity_name = True
    _attr_device_class = SwitchDeviceClass.SWITCH

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}


class DeskyChildLockSwitch(_DeskySwitch):
    """Child lock on / off."""

    _attr_name = "Child Lock"
    _attr_icon = "mdi:lock"

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_child_lock"

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.desk_state.lock_status
        return bool(val) if val is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_lock(1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_lock(0)


class DeskyVibrationSwitch(_DeskySwitch):
    """Vibration on / off."""

    _attr_name = "Vibration"
    _attr_icon = "mdi:vibrate"

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_vibration"

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.desk_state.vibration
        return bool(val) if val is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_vibration(1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_vibration(0)


class DeskyLightingSwitch(_DeskySwitch):
    """LED lighting on / off."""

    _attr_name = "LED Lighting"
    _attr_icon = "mdi:led-on"

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_lighting"

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.desk_state.lighting
        return bool(val) if val is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_lighting(1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.client.set_lighting(0)
