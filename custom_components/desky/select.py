"""Desky select entities (LED colour, anti-collision, touch mode)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ANTI_COLLISION_MAP,
    ANTI_COLLISION_REVERSE_MAP,
    DOMAIN,
    LED_COLOR_MAP,
    LED_COLOR_REVERSE_MAP,
    TOUCH_MODE_MAP,
    TOUCH_MODE_REVERSE_MAP,
)
from .coordinator import DeskyCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DeskyCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            DeskyLedColorSelect(coordinator, entry),
            DeskyAntiCollisionSelect(coordinator, entry),
            DeskyTouchModeSelect(coordinator, entry),
        ]
    )


class DeskyLedColorSelect(CoordinatorEntity[DeskyCoordinator], SelectEntity):
    """LED colour selector."""

    _attr_has_entity_name = True
    _attr_name = "LED Color"
    _attr_icon = "mdi:palette"
    _attr_options = list(LED_COLOR_MAP.values())

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_led_color"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    @property
    def current_option(self) -> str | None:
        val = self.coordinator.desk_state.led_color
        return LED_COLOR_MAP.get(val) if val is not None else None

    async def async_select_option(self, option: str) -> None:
        code = LED_COLOR_REVERSE_MAP.get(option)
        if code is not None:
            await self.coordinator.client.set_led_color(code)


class DeskyAntiCollisionSelect(CoordinatorEntity[DeskyCoordinator], SelectEntity):
    """Anti-collision sensitivity selector."""

    _attr_has_entity_name = True
    _attr_name = "Anti-Collision Sensitivity"
    _attr_icon = "mdi:shield-alert"
    _attr_options = list(ANTI_COLLISION_MAP.values())

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_anti_collision"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    @property
    def current_option(self) -> str | None:
        val = self.coordinator.desk_state.anti_collision
        return ANTI_COLLISION_MAP.get(val) if val is not None else None

    async def async_select_option(self, option: str) -> None:
        code = ANTI_COLLISION_REVERSE_MAP.get(option)
        if code is not None:
            await self.coordinator.client.set_anti_collision(code)


class DeskyTouchModeSelect(CoordinatorEntity[DeskyCoordinator], SelectEntity):
    """Touch mode selector."""

    _attr_has_entity_name = True
    _attr_name = "Touch Mode"
    _attr_icon = "mdi:gesture-tap"
    _attr_options = list(TOUCH_MODE_MAP.values())

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_touch_mode"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    @property
    def current_option(self) -> str | None:
        val = self.coordinator.desk_state.touch_mode
        return TOUCH_MODE_MAP.get(val) if val is not None else None

    async def async_select_option(self, option: str) -> None:
        code = TOUCH_MODE_REVERSE_MAP.get(option)
        if code is not None:
            await self.coordinator.client.set_touch_mode(code)
