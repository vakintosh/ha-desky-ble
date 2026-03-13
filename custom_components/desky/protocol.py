from __future__ import annotations

import dataclasses
import enum
import logging

_LOGGER = logging.getLogger(__name__)

HEADER_TX = bytes([0xF1, 0xF1])
HEADER_RX = bytes([0xF2, 0xF2])
FOOTER_TX = 0x7E


class Opcode(enum.IntEnum):
    """Command opcodes extracted from the Desky APK."""

    MOVE_UP = 0x01
    MOVE_DOWN = 0x02
    SAVE_MEMORY_1 = 0x03
    SAVE_MEMORY_2 = 0x04
    RECALL_MEMORY_1 = 0x05
    RECALL_MEMORY_2 = 0x06
    GET_STATUS = 0x07
    GET_LIMIT = 0x0C
    SET_UNIT = 0x0E
    SET_TOUCH_MODE = 0x19
    MOVE_TO_HEIGHT = 0x1B
    SET_ANTI_COLLISION = 0x1D
    SET_HIGHEST_LIMIT = 0x21
    SET_LOWEST_LIMIT = 0x22
    CLEAR_LIMIT = 0x23
    SAVE_MEMORY_3 = 0x25
    SAVE_MEMORY_4 = 0x26
    RECALL_MEMORY_3 = 0x27
    RECALL_MEMORY_4 = 0x28
    STOP = 0x2B
    SET_REMINDER = 0xB1
    SET_LOCK = 0xB2
    SET_VIBRATION = 0xB3
    SET_LED_COLOR = 0xB4
    SET_LIGHTING = 0xB5
    SET_BRIGHTNESS = 0xB6
    HANDSHAKE = 0xFE


_DUAL_OPCODES = {
    Opcode.SET_ANTI_COLLISION,
    Opcode.SET_LOCK,
    Opcode.SET_VIBRATION,
    Opcode.SET_LED_COLOR,
    Opcode.SET_LIGHTING,
    Opcode.SET_BRIGHTNESS,
}


def _checksum(cmd: int, length: int, data: bytes) -> int:
    """Compute the additive checksum over cmd + length + data."""
    return (cmd + length + sum(data)) & 0xFF


def height_cm_to_raw(height_cm: float) -> int:
    """Convert a height in *cm* to the raw protocol value (× 10)."""
    return int(round(height_cm * 10))


def height_raw_to_cm(raw: int) -> float:
    """Convert raw protocol value back to cm."""
    return raw / 10.0


def height_is_cm(raw: int) -> bool:
    """Return True if the raw value represents centimetres (≥ 550)."""
    return raw >= 550


def build_frame(opcode: int, data: bytes = b"") -> bytes:
    """Build a complete TX frame ready to write to the BLE characteristic.

    Returns
    -------
    bytes
        ``[0xF1, 0xF1, CMD, LEN, *DATA, CHECKSUM, 0x7E]``
    """
    length = len(data)
    cs = _checksum(opcode, length, data)
    return HEADER_TX + bytes([opcode, length]) + data + bytes([cs, FOOTER_TX])


CMD_MOVE_UP = build_frame(Opcode.MOVE_UP)
CMD_MOVE_DOWN = build_frame(Opcode.MOVE_DOWN)
CMD_STOP = build_frame(Opcode.STOP)
CMD_RECALL_MEMORY_1 = build_frame(Opcode.RECALL_MEMORY_1)
CMD_RECALL_MEMORY_2 = build_frame(Opcode.RECALL_MEMORY_2)
CMD_RECALL_MEMORY_3 = build_frame(Opcode.RECALL_MEMORY_3)
CMD_RECALL_MEMORY_4 = build_frame(Opcode.RECALL_MEMORY_4)
CMD_SAVE_MEMORY_1 = build_frame(Opcode.SAVE_MEMORY_1)
CMD_SAVE_MEMORY_2 = build_frame(Opcode.SAVE_MEMORY_2)
CMD_SAVE_MEMORY_3 = build_frame(Opcode.SAVE_MEMORY_3)
CMD_SAVE_MEMORY_4 = build_frame(Opcode.SAVE_MEMORY_4)
CMD_GET_STATUS = build_frame(Opcode.GET_STATUS)
CMD_GET_LIMIT = build_frame(Opcode.GET_LIMIT)
CMD_CLEAR_LIMIT = build_frame(Opcode.CLEAR_LIMIT)
CMD_HANDSHAKE = build_frame(Opcode.HANDSHAKE)

CMD_GET_ANTI_COLLISION = build_frame(Opcode.SET_ANTI_COLLISION)
CMD_GET_LOCK = build_frame(Opcode.SET_LOCK)
CMD_GET_VIBRATION = build_frame(Opcode.SET_VIBRATION)
CMD_GET_LED_COLOR = build_frame(Opcode.SET_LED_COLOR)
CMD_GET_LIGHTING = build_frame(Opcode.SET_LIGHTING)
CMD_GET_BRIGHTNESS = build_frame(Opcode.SET_BRIGHTNESS)
CMD_GET_CURRENT_LIMITATION = build_frame(0x20)


def cmd_move_to_height(raw_height: int) -> bytes:
    """Build a move-to-height command (raw = cm × 10)."""
    data = bytes([(raw_height >> 8) & 0xFF, raw_height & 0xFF])
    return build_frame(Opcode.MOVE_TO_HEIGHT, data)


def cmd_set_highest_limit(raw_height: int) -> bytes:
    data = bytes([(raw_height >> 8) & 0xFF, raw_height & 0xFF])
    return build_frame(Opcode.SET_HIGHEST_LIMIT, data)


def cmd_set_lowest_limit(raw_height: int) -> bytes:
    data = bytes([(raw_height >> 8) & 0xFF, raw_height & 0xFF])
    return build_frame(Opcode.SET_LOWEST_LIMIT, data)


def cmd_set_value(opcode: int, value: int) -> bytes:
    """Build a single-byte-value set command."""
    return build_frame(opcode, bytes([value & 0xFF]))


def cmd_set_touch_mode(value: int) -> bytes:
    return cmd_set_value(Opcode.SET_TOUCH_MODE, value)


def cmd_set_unit(value: int) -> bytes:
    return cmd_set_value(Opcode.SET_UNIT, value)


def cmd_set_brightness(value: int) -> bytes:
    return cmd_set_value(Opcode.SET_BRIGHTNESS, value)


def cmd_set_led_color(value: int) -> bytes:
    return cmd_set_value(Opcode.SET_LED_COLOR, value)


def cmd_set_vibration(value: int) -> bytes:
    return cmd_set_value(Opcode.SET_VIBRATION, value)


def cmd_set_lock(value: int) -> bytes:
    return cmd_set_value(Opcode.SET_LOCK, value)


def cmd_set_lighting(value: int) -> bytes:
    return cmd_set_value(Opcode.SET_LIGHTING, value)


def cmd_set_anti_collision(value: int) -> bytes:
    return cmd_set_value(Opcode.SET_ANTI_COLLISION, value)


def cmd_set_reminder(minutes: int) -> bytes:
    return cmd_set_value(Opcode.SET_REMINDER, minutes)


@dataclasses.dataclass(slots=True)
class DeskState:
    """Mutable snapshot of all known desk state."""

    height_raw: int | None = None
    is_moving: bool = False
    lock_status: int | None = None  # 0=off, 1=on
    brightness: int | None = None  # 0-100
    led_color: int | None = None  # 1-7
    vibration: int | None = None  # 0=off, 1=on
    lighting: int | None = None  # 0=off, 1=on
    anti_collision: int | None = None  # 1-3
    touch_mode: int | None = None  # 0=one-press, 1=hold
    upper_limit_raw: int | None = None
    lower_limit_raw: int | None = None
    has_limits: bool = False

    @property
    def height_cm(self) -> float | None:
        if self.height_raw is None:
            return None
        return height_raw_to_cm(self.height_raw)


def parse_notification(data: bytes | bytearray, state: DeskState) -> bool:
    """Parse a BLE notification payload and update *state* in-place.

    Returns ``True`` if the notification was recognised and handled.
    """
    hex_str = data.hex().upper()

    if len(hex_str) < 12:
        return False

    header = hex_str[:4]
    if header != "F2F2":
        return False

    cmd_str = hex_str[4:6]
    len_str = hex_str[6:8]
    cmd = int(cmd_str, 16)
    data_len = int(len_str, 16)

    if cmd == 0x01 and data_len == 0x03 and len(hex_str) >= 12:
        raw = int(hex_str[8:12], 16)
        state.height_raw = raw
        state.is_moving = True
        return True

    if cmd == 0x21 and data_len == 0x02 and len(hex_str) >= 12:
        state.upper_limit_raw = int(hex_str[8:12], 16)
        state.has_limits = True
        return True

    if cmd == 0x22 and data_len == 0x02 and len(hex_str) >= 12:
        state.lower_limit_raw = int(hex_str[8:12], 16)
        state.has_limits = True
        return True

    if cmd == 0x20 and data_len == 0x01 and len(hex_str) >= 10:
        status = int(hex_str[8:10], 16)
        state.has_limits = status != 0x00
        return True

    if cmd == 0x1D and data_len == 0x01 and len(hex_str) >= 10:
        state.anti_collision = int(hex_str[8:10], 16)
        return True

    if cmd == 0xB2 and data_len == 0x01 and len(hex_str) >= 10:
        state.lock_status = int(hex_str[8:10], 16)
        return True

    if cmd == 0xB6 and data_len == 0x01 and len(hex_str) >= 10:
        state.brightness = int(hex_str[8:10], 16)
        return True

    if cmd == 0xB4 and data_len == 0x01 and len(hex_str) >= 10:
        state.led_color = int(hex_str[8:10], 16)
        return True

    if cmd == 0xB3 and data_len == 0x01 and len(hex_str) >= 10:
        state.vibration = int(hex_str[8:10], 16)
        return True

    if cmd == 0xB5 and data_len == 0x01 and len(hex_str) >= 10:
        state.lighting = int(hex_str[8:10], 16)
        return True

    if cmd == 0x19 and data_len == 0x01 and len(hex_str) >= 10:
        state.touch_mode = int(hex_str[8:10], 16)
        return True

    _LOGGER.debug("Unhandled notification: %s", hex_str)
    return False
