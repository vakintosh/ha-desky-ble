from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    entities: list[ButtonEntity] = []

    for slot in range(1, 5):
        entities.append(DeskyRecallPresetButton(coordinator, entry, slot))
        entities.append(DeskySavePresetButton(coordinator, entry, slot))

    async_add_entities(entities)


class DeskyRecallPresetButton(CoordinatorEntity[DeskyCoordinator], ButtonEntity):
    """Button that recalls a stored memory preset."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:bookmark-outline"

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: ConfigEntry,
        slot: int,
    ) -> None:
        super().__init__(coordinator)
        self._slot = slot
        self._attr_unique_id = f"{entry.entry_id}_recall_preset_{slot}"
        self._attr_name = f"Preset {slot}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    async def async_press(self) -> None:
        await self.coordinator.client.recall_memory(self._slot)


class DeskySavePresetButton(CoordinatorEntity[DeskyCoordinator], ButtonEntity):
    """Button that saves the current height to a memory slot."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:bookmark-plus"
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: DeskyCoordinator,
        entry: ConfigEntry,
        slot: int,
    ) -> None:
        super().__init__(coordinator)
        self._slot = slot
        self._attr_unique_id = f"{entry.entry_id}_save_preset_{slot}"
        self._attr_name = f"Save Preset {slot}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    async def async_press(self) -> None:
        await self.coordinator.client.save_memory(self._slot)
