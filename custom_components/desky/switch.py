"""Support for Desky BLE standing desk switch platform."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DeskyConfigEntry
from .const import DOMAIN
from .coordinator import DeskyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DeskyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Desky switch platform."""
    coordinator = entry.runtime_data
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
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        address = entry.data[CONF_ADDRESS]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
        )
        self._address = address


class DeskyChildLockSwitch(_DeskySwitch):
    """Child lock on / off."""

    _attr_translation_key = "child_lock"

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._address}_child_lock"

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.desk_state.lock_status
        return bool(val) if val is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the child lock."""
        await self.coordinator.client.set_lock(1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the child lock."""
        await self.coordinator.client.set_lock(0)


class DeskyVibrationSwitch(_DeskySwitch):
    """Vibration on / off."""

    _attr_translation_key = "vibration"

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._address}_vibration"

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.desk_state.vibration
        return bool(val) if val is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on vibration."""
        await self.coordinator.client.set_vibration(1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off vibration."""
        await self.coordinator.client.set_vibration(0)


class DeskyLightingSwitch(_DeskySwitch):
    """LED lighting on / off."""

    _attr_translation_key = "led_lighting"

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._address}_lighting"

    @property
    def is_on(self) -> bool | None:
        val = self.coordinator.desk_state.lighting
        return bool(val) if val is not None else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on LED lighting."""
        await self.coordinator.client.set_lighting(1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off LED lighting."""
        await self.coordinator.client.set_lighting(0)
