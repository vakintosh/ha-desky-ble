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
    "homeassistant.config_entries",
    "homeassistant.const",
    "homeassistant.core",
    "homeassistant.data_entry_flow",
    "homeassistant.exceptions",
    "homeassistant.helpers",
    "homeassistant.helpers.entity_platform",
    "homeassistant.helpers.update_coordinator",
    "voluptuous",
]

for mod_name in _MOCK_MODULES:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()
