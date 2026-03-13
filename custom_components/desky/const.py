"""Constants for the Desky BLE standing desk integration."""

from __future__ import annotations

from desky_ble.ble_client import ALL_SERVICE_UUIDS

DOMAIN = "desky"
DEFAULT_NAME = "Desky Standing Desk"

DEFAULT_MIN_HEIGHT_CM = 60.0
DEFAULT_MAX_HEIGHT_CM = 124.0
DEFAULT_MIN_HEIGHT_IN = 24.0
DEFAULT_MAX_HEIGHT_IN = 48.0

HEIGHT_UNIT_THRESHOLD = 55.0

LED_COLOR_WHITE = 1
LED_COLOR_RED = 2
LED_COLOR_GREEN = 3
LED_COLOR_BLUE = 4
LED_COLOR_YELLOW = 5
LED_COLOR_PARTY = 6
LED_COLOR_OFF = 7

LED_COLOR_MAP: dict[int, str] = {
    LED_COLOR_WHITE: "White",
    LED_COLOR_RED: "Red",
    LED_COLOR_GREEN: "Green",
    LED_COLOR_BLUE: "Blue",
    LED_COLOR_YELLOW: "Yellow",
    LED_COLOR_PARTY: "Party Mode",
    LED_COLOR_OFF: "Off",
}

LED_COLOR_REVERSE_MAP: dict[str, int] = {v: k for k, v in LED_COLOR_MAP.items()}

ANTI_COLLISION_HIGH = 1
ANTI_COLLISION_MEDIUM = 2
ANTI_COLLISION_LOW = 3

ANTI_COLLISION_MAP: dict[int, str] = {
    ANTI_COLLISION_HIGH: "High",
    ANTI_COLLISION_MEDIUM: "Medium",
    ANTI_COLLISION_LOW: "Low",
}

ANTI_COLLISION_REVERSE_MAP: dict[str, int] = {
    v: k for k, v in ANTI_COLLISION_MAP.items()
}

TOUCH_MODE_ONE_PRESS = 0
TOUCH_MODE_PRESS_AND_HOLD = 1

TOUCH_MODE_MAP: dict[int, str] = {
    TOUCH_MODE_ONE_PRESS: "One Press",
    TOUCH_MODE_PRESS_AND_HOLD: "Press and Hold",
}

TOUCH_MODE_REVERSE_MAP: dict[str, int] = {v: k for k, v in TOUCH_MODE_MAP.items()}

CONF_UNIT = "unit"
CONF_POLL_INTERVAL = "poll_interval"
DEFAULT_POLL_INTERVAL = 30
