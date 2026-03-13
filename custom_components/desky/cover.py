"""Support for Desky BLE standing desk cover platform."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import (
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DeskyConfigEntry
from .const import DEFAULT_MAX_HEIGHT_CM, DEFAULT_MIN_HEIGHT_CM, DOMAIN
from .coordinator import DeskyCoordinator

from desky_ble import DeskState


async def async_setup_entry(
    hass: HomeAssistant,
    entry: DeskyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Desky cover platform."""
    async_add_entities([DeskyCover(entry.runtime_data, entry)])


class DeskyCover(CoordinatorEntity[DeskyCoordinator], CoverEntity):
    """Cover entity representing the Desky standing desk."""

    _attr_supported_features = (
        CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.SET_POSITION
    )
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{address}_cover"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=entry.title,
            manufacturer="Desky",
            model="Standing Desk",
        )
        self._min_raw = int(DEFAULT_MIN_HEIGHT_CM * 10)
        self._max_raw = int(DEFAULT_MAX_HEIGHT_CM * 10)
        self._prev_height_raw: int | None = None
        self._moving_up: bool | None = None

    @property
    def _desk(self) -> DeskState:
        return self.coordinator.desk_state

    @property
    def current_cover_position(self) -> int | None:
        if self._desk.height_raw is None:
            return None
        span = self._max_raw - self._min_raw
        if span <= 0:
            return 0
        pos = int(((self._desk.height_raw - self._min_raw) / span) * 100)
        return max(0, min(100, pos))

    @property
    def is_closed(self) -> bool:
        return self.current_cover_position == 0

    @property
    def is_opening(self) -> bool:
        return self._desk.is_moving and self._moving_up is True

    @property
    def is_closing(self) -> bool:
        return self._desk.is_moving and self._moving_up is False

    async def async_open_cover(self, **kwargs: Any) -> None:
        await self.coordinator.client.move_up()

    async def async_close_cover(self, **kwargs: Any) -> None:
        await self.coordinator.client.move_down()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        await self.coordinator.client.stop()
        self._desk.is_moving = False
        self.async_write_ha_state()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        position: int = kwargs.get("position", 50)
        span = self._max_raw - self._min_raw
        raw = self._min_raw + int((position / 100) * span)
        await self.coordinator.client.move_to_height(raw)

    @callback
    def _handle_coordinator_update(self) -> None:
        state = self._desk
        if state.upper_limit_raw is not None:
            self._max_raw = state.upper_limit_raw
        if state.lower_limit_raw is not None:
            self._min_raw = state.lower_limit_raw

        current = state.height_raw
        if (
            state.is_moving
            and current is not None
            and self._prev_height_raw is not None
        ):
            delta = current - self._prev_height_raw
            if delta > 0:
                self._moving_up = True
            elif delta < 0:
                self._moving_up = False
        elif not state.is_moving:
            self._moving_up = None

        self._prev_height_raw = current
        self.async_write_ha_state()
