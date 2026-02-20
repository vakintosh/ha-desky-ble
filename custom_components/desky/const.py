"""Constants for the Desky standing desk integration."""

from __future__ import annotations

DOMAIN = "desky"
DEFAULT_NAME = "Desky Standing Desk"

# ---------------------------------------------------------------------------
# BLE Service / Characteristic UUIDs (3 controller variants)
# ---------------------------------------------------------------------------

# Lierda variant 1 (service1 / ff12)
UUID_SERVICE_LIERDA1 = "0000ff12-0000-1000-8000-00805f9b34fb"
UUID_CHAR_WRITE_LIERDA1 = "0000ff01-0000-1000-8000-00805f9b34fb"
UUID_CHAR_READ_LIERDA1 = "0000ff02-0000-1000-8000-00805f9b34fb"
UUID_CHAR_BTNAME_LIERDA1 = "0000ff06-0000-1000-8000-00805f9b34fb"

# Lierda variant 2 (service3 / fe60)
UUID_SERVICE_LIERDA2 = "0000fe60-0000-1000-8000-00805f9b34fb"
UUID_CHAR_WRITE_LIERDA2 = "0000fe61-0000-1000-8000-00805f9b34fb"
UUID_CHAR_READ_LIERDA2 = "0000fe62-0000-1000-8000-00805f9b34fb"
UUID_CHAR_SET_LIERDA2 = "0000fe63-0000-1000-8000-00805f9b34fb"

# Peilin variant (service2 / 88121427)
UUID_SERVICE_PEILIN = "88121427-11e2-52a2-4615-ff00dec16800"
UUID_CHAR_RW_PEILIN = "88121427-11e2-52a2-4615-ff00dec16801"

# Login/auth service (used by Peilin controllers)
UUID_SERVICE_LOGIN = "9e5d1e47-5c13-43a0-8635-82adffc0386f"
UUID_CHAR_LOGIN_WRITE = "9e5d1e47-5c13-43a0-8635-82adffc1386f"

# CCCD descriptor for enabling notifications
UUID_CCCD = "00002902-0000-1000-8000-00805f9b34fb"

# Login payload sent on connection
LOGIN_PAYLOAD = bytes([0x01, 0x16, 0x02, 0x38, 0x38, 0x38, 0x38])

# ---------------------------------------------------------------------------
# All discoverable service UUIDs (for BLE scanning / manifest matching)
# ---------------------------------------------------------------------------
ALL_SERVICE_UUIDS: list[str] = [
    UUID_SERVICE_LIERDA1,
    UUID_SERVICE_LIERDA2,
    UUID_SERVICE_PEILIN,
]

# ---------------------------------------------------------------------------
# Desk height defaults (in tenths – i.e. raw protocol values)
# ---------------------------------------------------------------------------
DEFAULT_MIN_HEIGHT_CM = 60.0
DEFAULT_MAX_HEIGHT_CM = 124.0
DEFAULT_MIN_HEIGHT_IN = 24.0
DEFAULT_MAX_HEIGHT_IN = 48.0

# Threshold to distinguish cm vs inches (raw / 10)
HEIGHT_UNIT_THRESHOLD = 55.0

# ---------------------------------------------------------------------------
# LED colour codes (as sent over BLE)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Anti-collision sensitivity levels
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Touch mode options
# ---------------------------------------------------------------------------
TOUCH_MODE_ONE_PRESS = 0
TOUCH_MODE_PRESS_AND_HOLD = 1

TOUCH_MODE_MAP: dict[int, str] = {
    TOUCH_MODE_ONE_PRESS: "One Press",
    TOUCH_MODE_PRESS_AND_HOLD: "Press and Hold",
}

TOUCH_MODE_REVERSE_MAP: dict[str, int] = {v: k for k, v in TOUCH_MODE_MAP.items()}

# ---------------------------------------------------------------------------
# Config / options keys
# ---------------------------------------------------------------------------
CONF_UNIT = "unit"
CONF_POLL_INTERVAL = "poll_interval"
DEFAULT_POLL_INTERVAL = 30  # seconds
