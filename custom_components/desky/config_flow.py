"""Config flow for Desky Standing Desk (BLE)."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    ALL_SERVICE_UUIDS,
    CONF_POLL_INTERVAL,
    CONF_UNIT,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _match_service_uuids(service_info: BluetoothServiceInfoBleak) -> bool:
    """Return True if *service_info* advertises a known Desky service UUID."""
    adv_uuids = {u.lower() for u in service_info.service_uuids}
    return any(u.lower() in adv_uuids for u in ALL_SERVICE_UUIDS)


class DeskyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Desky Standing Desk."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovery_info: BluetoothServiceInfoBleak | None = None

    # ------------------------------------------------------------------
    # Bluetooth passive discovery
    # ------------------------------------------------------------------
    async def async_step_bluetooth(
        self,
        discovery_info: BluetoothServiceInfoBleak,
    ) -> FlowResult:
        """Handle a desk discovered via BLE."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Confirm the discovered device."""
        if self._discovery_info is None:
            return self.async_abort(reason="no_devices_found")

        if user_input is not None:
            return self.async_create_entry(
                title=self._discovery_info.name or "Desky Desk",
                data={CONF_ADDRESS: self._discovery_info.address},
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={
                "name": self._discovery_info.name or self._discovery_info.address,
            },
        )

    # ------------------------------------------------------------------
    # Manual entry
    # ------------------------------------------------------------------
    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle manual configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Desky ({address})",
                data={CONF_ADDRESS: address},
            )

        # Try to show discovered devices as suggestions
        discovered: list[BluetoothServiceInfoBleak] = async_discovered_service_info(
            self.hass
        )
        desks = [d for d in discovered if _match_service_uuids(d)]

        if desks:
            _LOGGER.debug("Found %d Desky desk(s) via BLE scan", len(desks))

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): str}),
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Options flow
    # ------------------------------------------------------------------
    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> DeskyOptionsFlow:
        return DeskyOptionsFlow(config_entry)


class DeskyOptionsFlow(OptionsFlow):
    """Options flow for Desky integration."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UNIT,
                        default=self._config_entry.options.get(CONF_UNIT, "cm"),
                    ): vol.In(["cm", "inches"]),
                    vol.Optional(
                        CONF_POLL_INTERVAL,
                        default=self._config_entry.options.get(
                            CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
                        ),
                    ): vol.All(int, vol.Range(min=5, max=300)),
                }
            ),
        )
