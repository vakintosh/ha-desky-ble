"""Tests for the Desky BLE protocol encoder / decoder."""

from __future__ import annotations

from custom_components.desky.protocol import (
    CMD_HANDSHAKE,
    CMD_MOVE_DOWN,
    CMD_MOVE_UP,
    CMD_RECALL_MEMORY_1,
    CMD_RECALL_MEMORY_2,
    CMD_RECALL_MEMORY_3,
    CMD_RECALL_MEMORY_4,
    CMD_SAVE_MEMORY_1,
    CMD_SAVE_MEMORY_2,
    CMD_STOP,
    DeskState,
    cmd_move_to_height,
    cmd_set_brightness,
    cmd_set_led_color,
    cmd_set_lock,
    cmd_set_value,
    height_cm_to_raw,
    height_is_cm,
    height_raw_to_cm,
    parse_notification,
)


class TestFrameEncoding:
    """Verify frame encoding matches the APK-extracted byte sequences."""

    def test_move_up(self) -> None:
        # APK: {-15, -15, 1, 0, 1, 126} → signed → F1 F1 01 00 01 7E
        assert bytes([0xF1, 0xF1, 0x01, 0x00, 0x01, 0x7E]) == CMD_MOVE_UP

    def test_move_down(self) -> None:
        assert bytes([0xF1, 0xF1, 0x02, 0x00, 0x02, 0x7E]) == CMD_MOVE_DOWN

    def test_stop(self) -> None:
        # APK: opcode 0x2B
        assert bytes([0xF1, 0xF1, 0x2B, 0x00, 0x2B, 0x7E]) == CMD_STOP

    def test_recall_memory_1(self) -> None:
        assert bytes([0xF1, 0xF1, 0x05, 0x00, 0x05, 0x7E]) == CMD_RECALL_MEMORY_1

    def test_recall_memory_2(self) -> None:
        assert bytes([0xF1, 0xF1, 0x06, 0x00, 0x06, 0x7E]) == CMD_RECALL_MEMORY_2

    def test_recall_memory_3(self) -> None:
        assert bytes([0xF1, 0xF1, 0x27, 0x00, 0x27, 0x7E]) == CMD_RECALL_MEMORY_3

    def test_recall_memory_4(self) -> None:
        assert bytes([0xF1, 0xF1, 0x28, 0x00, 0x28, 0x7E]) == CMD_RECALL_MEMORY_4

    def test_save_memory_1(self) -> None:
        assert bytes([0xF1, 0xF1, 0x03, 0x00, 0x03, 0x7E]) == CMD_SAVE_MEMORY_1

    def test_save_memory_2(self) -> None:
        assert bytes([0xF1, 0xF1, 0x04, 0x00, 0x04, 0x7E]) == CMD_SAVE_MEMORY_2

    def test_handshake(self) -> None:
        assert bytes([0xF1, 0xF1, 0xFE, 0x00, 0xFE, 0x7E]) == CMD_HANDSHAKE

    def test_move_to_height_75cm(self) -> None:
        # 75.0 cm × 10 = 750 = 0x02EE
        frame = cmd_move_to_height(750)
        assert frame[0:2] == bytes([0xF1, 0xF1])
        assert frame[2] == 0x1B  # opcode
        assert frame[3] == 0x02  # length
        assert frame[4] == 0x02  # high byte
        assert frame[5] == 0xEE  # low byte
        # checksum = 0x1B + 0x02 + 0x02 + 0xEE = 0x10D → 0x0D
        assert frame[6] == (0x1B + 0x02 + 0x02 + 0xEE) & 0xFF
        assert frame[7] == 0x7E

    def test_move_to_height_100cm(self) -> None:
        # 100.0 cm × 10 = 1000 = 0x03E8
        frame = cmd_move_to_height(1000)
        assert frame[4] == 0x03
        assert frame[5] == 0xE8

    def test_set_brightness_50(self) -> None:
        frame = cmd_set_brightness(50)
        assert frame[2] == 0xB6  # opcode
        assert frame[3] == 0x01  # length
        assert frame[4] == 50

    def test_set_led_color_blue(self) -> None:
        frame = cmd_set_led_color(4)  # blue = 4
        assert frame[2] == 0xB4
        assert frame[4] == 4

    def test_set_lock_on(self) -> None:
        frame = cmd_set_lock(1)
        assert frame[2] == 0xB2
        assert frame[4] == 1

    def test_checksum_single_byte_value(self) -> None:
        # cmd_set_value builds [F1 F1 CMD 01 VAL CS 7E]
        # checksum = CMD + 1 + VAL
        frame = cmd_set_value(0x19, 0x01)  # touch mode one-press
        expected_cs = (0x19 + 0x01 + 0x01) & 0xFF
        assert frame[5] == expected_cs


class TestHeightConversions:
    def test_cm_to_raw(self) -> None:
        assert height_cm_to_raw(75.0) == 750
        assert height_cm_to_raw(60.0) == 600
        assert height_cm_to_raw(124.0) == 1240

    def test_raw_to_cm(self) -> None:
        assert height_raw_to_cm(750) == 75.0
        assert height_raw_to_cm(600) == 60.0
        assert height_raw_to_cm(1240) == 124.0

    def test_height_is_cm(self) -> None:
        assert height_is_cm(550) is True
        assert height_is_cm(600) is True
        assert height_is_cm(549) is False
        assert height_is_cm(244) is False


class TestNotificationParsing:
    def _make_state(self) -> DeskState:
        return DeskState()

    def test_height_notification(self) -> None:
        state = self._make_state()
        # F2F2 01 03 02EE (750 → 75.0 cm)
        data = bytes([0xF2, 0xF2, 0x01, 0x03, 0x02, 0xEE, 0x00])
        assert parse_notification(data, state) is True
        assert state.height_raw == 750
        assert state.height_cm == 75.0
        assert state.is_moving is True

    def test_upper_limit_notification(self) -> None:
        state = self._make_state()
        data = bytes([0xF2, 0xF2, 0x21, 0x02, 0x04, 0xD8, 0x00])  # 1240
        assert parse_notification(data, state) is True
        assert state.upper_limit_raw == 1240
        assert state.has_limits is True

    def test_lower_limit_notification(self) -> None:
        state = self._make_state()
        data = bytes([0xF2, 0xF2, 0x22, 0x02, 0x02, 0x58, 0x00])  # 600
        assert parse_notification(data, state) is True
        assert state.lower_limit_raw == 600

    def test_lock_status_notification(self) -> None:
        state = self._make_state()
        data = bytes([0xF2, 0xF2, 0xB2, 0x01, 0x01, 0x00])
        assert parse_notification(data, state) is True
        assert state.lock_status == 1

    def test_brightness_notification(self) -> None:
        state = self._make_state()
        data = bytes([0xF2, 0xF2, 0xB6, 0x01, 0x32, 0x00])  # 50
        assert parse_notification(data, state) is True
        assert state.brightness == 50

    def test_led_color_notification(self) -> None:
        state = self._make_state()
        data = bytes([0xF2, 0xF2, 0xB4, 0x01, 0x04, 0x00])  # blue
        assert parse_notification(data, state) is True
        assert state.led_color == 4

    def test_vibration_notification(self) -> None:
        state = self._make_state()
        data = bytes([0xF2, 0xF2, 0xB3, 0x01, 0x01, 0x00])
        assert parse_notification(data, state) is True
        assert state.vibration == 1

    def test_lighting_notification(self) -> None:
        state = self._make_state()
        data = bytes([0xF2, 0xF2, 0xB5, 0x01, 0x01, 0x00])
        assert parse_notification(data, state) is True
        assert state.lighting == 1

    def test_anti_collision_notification(self) -> None:
        state = self._make_state()
        data = bytes([0xF2, 0xF2, 0x1D, 0x01, 0x02, 0x00])
        assert parse_notification(data, state) is True
        assert state.anti_collision == 2

    def test_touch_mode_notification(self) -> None:
        state = self._make_state()
        data = bytes([0xF2, 0xF2, 0x19, 0x01, 0x00, 0x00])
        assert parse_notification(data, state) is True
        assert state.touch_mode == 0

    def test_unrecognised_notification(self) -> None:
        state = self._make_state()
        data = bytes([0xF2, 0xF2, 0xFF, 0x00, 0x00, 0x00])
        assert parse_notification(data, state) is False

    def test_too_short_notification(self) -> None:
        state = self._make_state()
        data = bytes([0xF2, 0xF2])
        assert parse_notification(data, state) is False

    def test_wrong_header(self) -> None:
        state = self._make_state()
        data = bytes([0xAA, 0xBB, 0x01, 0x03, 0x02, 0xEE, 0x00])
        assert parse_notification(data, state) is False
