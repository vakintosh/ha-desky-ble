"""Support for Desky BLE standing desk button platform."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
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
    """Set up Desky button platform."""
    coordinator = entry.runtime_data
    entities: list[ButtonEntity] = []

    for slot in range(1, 5):
        entities.append(DeskyRecallPresetButton(coordinator, entry, slot))
        entities.append(DeskySavePresetButton(coordinator, entry, slot))

    async_add_entities(entities)


class DeskyRecallPresetButton(CoordinatorEntity[DeskyCoordinator], ButtonEntity):
    """Button that recalls a stored memory preset."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
        slot: int,
    ) -> None:
        super().__init__(coordinator)
        self._slot = slot
        address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{address}_recall_preset_{slot}"
        self._attr_translation_key = f"recall_preset_{slot}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
        )

    async def async_press(self) -> None:
        """Recall a memory preset."""
        await self.coordinator.client.recall_memory(self._slot)


class DeskySavePresetButton(CoordinatorEntity[DeskyCoordinator], ButtonEntity):
    """Button that saves the current height to a memory slot."""

    _attr_has_entity_name = True
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: DeskyConfigEntry,
        slot: int,
    ) -> None:
        super().__init__(coordinator)
        self._slot = slot
        address = entry.data[CONF_ADDRESS]
        self._attr_unique_id = f"{address}_save_preset_{slot}"
        self._attr_translation_key = f"save_preset_{slot}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
        )

    async def async_press(self) -> None:
        """Save the current height to a memory slot."""
        await self.coordinator.client.save_memory(self._slot)
