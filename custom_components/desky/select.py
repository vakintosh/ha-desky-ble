"""Support for Desky BLE standing desk select platform."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DeskyConfigEntry
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

_LOGGER = logging.getLogger(__name__)

DEBOUNCE_SECONDS = 0.5


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DeskyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Desky select platform."""
    coordinator = entry.runtime_data
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
    _attr_translation_key = "led_color"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = list(LED_COLOR_MAP.values())

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{address}_led_color"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
        )
        self._debounce_handle: asyncio.TimerHandle | None = None

    @property
    def current_option(self) -> str | None:
        val = self.coordinator.desk_state.led_color
        return LED_COLOR_MAP.get(val) if val is not None else None

    async def async_select_option(self, option: str) -> None:
        """Set the LED color (debounced)."""
        code = LED_COLOR_REVERSE_MAP.get(option)
        if code is not None:
            _debounce_call(self, lambda: self.coordinator.client.set_led_color(code))


class DeskyAntiCollisionSelect(CoordinatorEntity[DeskyCoordinator], SelectEntity):
    """Anti-collision sensitivity selector."""

    _attr_has_entity_name = True
    _attr_translation_key = "anti_collision"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = list(ANTI_COLLISION_MAP.values())

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{address}_anti_collision"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
        )
        self._debounce_handle: asyncio.TimerHandle | None = None

    @property
    def current_option(self) -> str | None:
        val = self.coordinator.desk_state.anti_collision
        return ANTI_COLLISION_MAP.get(val) if val is not None else None

    async def async_select_option(self, option: str) -> None:
        """Set the anti-collision sensitivity (debounced)."""
        code = ANTI_COLLISION_REVERSE_MAP.get(option)
        if code is not None:
            _debounce_call(
                self, lambda: self.coordinator.client.set_anti_collision(code)
            )


class DeskyTouchModeSelect(CoordinatorEntity[DeskyCoordinator], SelectEntity):
    """Touch mode selector."""

    _attr_has_entity_name = True
    _attr_translation_key = "touch_mode"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = list(TOUCH_MODE_MAP.values())

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{address}_touch_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
        )
        self._debounce_handle: asyncio.TimerHandle | None = None

    @property
    def current_option(self) -> str | None:
        val = self.coordinator.desk_state.touch_mode
        return TOUCH_MODE_MAP.get(val) if val is not None else None

    async def async_select_option(self, option: str) -> None:
        """Set the touch mode (debounced)."""
        code = TOUCH_MODE_REVERSE_MAP.get(option)
        if code is not None:
            _debounce_call(self, lambda: self.coordinator.client.set_touch_mode(code))


def _debounce_call(
    entity: DeskyLedColorSelect | DeskyAntiCollisionSelect | DeskyTouchModeSelect,
    coro_factory: Callable[[], Coroutine[Any, Any, None]],
) -> None:
    """Cancel any pending debounce timer and schedule a new one."""
    if entity._debounce_handle is not None:
        entity._debounce_handle.cancel()
    loop = asyncio.get_running_loop()
    entity._debounce_handle = loop.call_later(
        DEBOUNCE_SECONDS,
        lambda: asyncio.ensure_future(coro_factory()),
    )
