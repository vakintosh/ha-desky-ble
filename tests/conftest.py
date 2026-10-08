"""pytest configuration – ensure custom_components is importable.

Stubs out homeassistant and related heavy dependencies so the pure-Python
protocol module can be tested standalone without a full HA installation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add the repo root so `custom_components.desky.protocol` is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ---------------------------------------------------------------------------
# Provide lightweight base classes for ConfigFlow / OptionsFlow so that
# classes inheriting from them keep their real method definitions instead of
# being swallowed by MagicMock.
# ---------------------------------------------------------------------------


class _FakeConfigFlow:
    """Minimal stand-in for homeassistant.config_entries.ConfigFlow."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        # Accept and ignore the `domain=` keyword argument.
        pass


class _FakeOptionsFlow:
    """Minimal stand-in for homeassistant.config_entries.OptionsFlow."""


_config_entries_mock = MagicMock()
_config_entries_mock.ConfigFlow = _FakeConfigFlow
_config_entries_mock.OptionsFlow = _FakeOptionsFlow
# ConfigEntry and ConfigFlowResult are only used as type hints – MagicMock is fine.
_config_entries_mock.ConfigEntry = MagicMock
_config_entries_mock.ConfigFlowResult = dict

# ---------------------------------------------------------------------------
# Provide lightweight base classes for entity platforms so that entity
# classes can be instantiated without the real HA runtime.
# ---------------------------------------------------------------------------


class _FakeEntity:
    """Minimal stand-in for homeassistant.helpers.entity.Entity."""

    _attr_has_entity_name = False
    _attr_name = None
    _attr_unique_id = None
    _attr_device_info = None
    _attr_entity_category = None
    _attr_translation_key = None
    _attr_entity_registry_enabled_default = True


class _FakeSensorEntity(_FakeEntity):
    _attr_device_class = None
    _attr_state_class = None
    _attr_native_unit_of_measurement = None


class _FakeCoverEntity(_FakeEntity):
    _attr_supported_features = 0


class _FakeSwitchEntity(_FakeEntity):
    _attr_device_class = None


class _FakeButtonEntity(_FakeEntity):
    pass


class _FakeSelectEntity(_FakeEntity):
    _attr_options = []


class _FakeNumberEntity(_FakeEntity):
    _attr_device_class = None
    _attr_native_unit_of_measurement = None
    _attr_mode = None
    _attr_native_step = None
    _attr_native_min_value = None
    _attr_native_max_value = None


class _FakeCoordinatorEntity:
    """Minimal stand-in for CoordinatorEntity."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        pass

    def __class_getitem__(cls, item: object) -> type:
        return cls

    def __init__(self, coordinator: object, *args: object, **kwargs: object) -> None:
        self.coordinator = coordinator

    def async_write_ha_state(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Stub out homeassistant and related packages that the integration imports
# at module level but are not needed for protocol-only tests.
# ---------------------------------------------------------------------------
_MOCK_MODULES = [
    "homeassistant",
    "homeassistant.components",
    "homeassistant.components.bluetooth",
    "homeassistant.components.cover",
    "homeassistant.components.sensor",
    "homeassistant.components.number",
    "homeassistant.components.button",
    "homeassistant.components.select",
    "homeassistant.components.switch",
    "homeassistant.const",
    "homeassistant.core",
    "homeassistant.data_entry_flow",
    "homeassistant.exceptions",
    "homeassistant.helpers",
    "homeassistant.helpers.device_registry",
    "homeassistant.helpers.entity",
    "homeassistant.helpers.entity_platform",
    "homeassistant.helpers.event",
    "homeassistant.helpers.update_coordinator",
    "voluptuous",
]

for mod_name in _MOCK_MODULES:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

# Provide real values for commonly used constants.
ha_const = sys.modules["homeassistant.const"]
ha_const.CONF_ADDRESS = "address"
ha_const.Platform = MagicMock()

# UnitOfLength for sensor/number
ha_const.UnitOfLength = MagicMock()
ha_const.UnitOfLength.CENTIMETERS = "cm"
ha_const.UnitOfLength.INCHES = "in"

# Sensor enums
sensor_mod = sys.modules["homeassistant.components.sensor"]
sensor_mod.SensorDeviceClass = MagicMock()
sensor_mod.SensorDeviceClass.DISTANCE = "distance"
sensor_mod.SensorStateClass = MagicMock()
sensor_mod.SensorStateClass.MEASUREMENT = "measurement"
sensor_mod.SensorEntity = _FakeSensorEntity

# Cover enums
cover_mod = sys.modules["homeassistant.components.cover"]
cover_mod.CoverEntity = _FakeCoverEntity
cover_mod.CoverEntityFeature = MagicMock()
cover_mod.CoverEntityFeature.OPEN = 1
cover_mod.CoverEntityFeature.CLOSE = 2
cover_mod.CoverEntityFeature.STOP = 4
cover_mod.CoverEntityFeature.SET_POSITION = 8

# Switch
switch_mod = sys.modules["homeassistant.components.switch"]
switch_mod.SwitchEntity = _FakeSwitchEntity
switch_mod.SwitchDeviceClass = MagicMock()
switch_mod.SwitchDeviceClass.SWITCH = "switch"

# Button
button_mod = sys.modules["homeassistant.components.button"]
button_mod.ButtonEntity = _FakeButtonEntity

# Select
select_mod = sys.modules["homeassistant.components.select"]
select_mod.SelectEntity = _FakeSelectEntity

# Number
number_mod = sys.modules["homeassistant.components.number"]
number_mod.NumberEntity = _FakeNumberEntity
number_mod.NumberDeviceClass = MagicMock()
number_mod.NumberDeviceClass.DISTANCE = "distance"
number_mod.NumberMode = MagicMock()
number_mod.NumberMode.SLIDER = "slider"

# Entity helpers
entity_mod = sys.modules["homeassistant.helpers.entity"]
entity_mod.EntityCategory = MagicMock()
entity_mod.EntityCategory.CONFIG = "config"

# DeviceInfo
device_reg_mod = sys.modules["homeassistant.helpers.device_registry"]
device_reg_mod.DeviceInfo = dict

# CoordinatorEntity
coord_mod = sys.modules["homeassistant.helpers.update_coordinator"]
coord_mod.CoordinatorEntity = _FakeCoordinatorEntity


class _FakeDataUpdateCoordinator:
    """Minimal subscriptable stand-in for DataUpdateCoordinator."""

    def __class_getitem__(cls, item: object) -> type:
        return cls

    def __init_subclass__(cls, **kwargs: object) -> None:
        pass

    def __init__(
        self,
        hass: object,
        logger: object,
        *,
        name: object = None,
        update_interval: object = None,
        **kwargs: object,
    ) -> None:
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval
        self.data = None
        self.last_update_success = True
        self.last_exception: object = None

    def async_set_updated_data(self, data: object) -> None:
        self.data = data
        self.last_update_success = True
        self.last_exception = None

    def async_set_update_error(self, err: object) -> None:
        self.last_update_success = False
        self.last_exception = err

    async def async_config_entry_first_refresh(self) -> None:
        self.data = await self._async_update_data()  # type: ignore[attr-defined]
        self.last_update_success = True


coord_mod.DataUpdateCoordinator = _FakeDataUpdateCoordinator
coord_mod.UpdateFailed = Exception

# Core callback
core_mod = sys.modules["homeassistant.core"]
core_mod.callback = lambda f: f


# Exceptions - must be real Exception subclasses for pytest.raises to work.
class _ConfigEntryNotReady(Exception):
    """Minimal stand-in for homeassistant.exceptions.ConfigEntryNotReady."""


exceptions_mod = sys.modules["homeassistant.exceptions"]
exceptions_mod.ConfigEntryNotReady = _ConfigEntryNotReady

# Install the config_entries stub *after* the loop so it takes priority.
sys.modules["homeassistant.config_entries"] = _config_entries_mock
