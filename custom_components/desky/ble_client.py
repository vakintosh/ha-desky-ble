"""Desky BLE client – handles connection, service discovery and commands.

Designed to work with Home Assistant's BLE proxy infrastructure
(bleak + bleak-retry-connector).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from enum import Enum, auto

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .const import (
    LOGIN_PAYLOAD,
    UUID_CHAR_LOGIN_WRITE,
    UUID_CHAR_READ_LIERDA1,
    UUID_CHAR_READ_LIERDA2,
    UUID_CHAR_RW_PEILIN,
    UUID_CHAR_WRITE_LIERDA1,
    UUID_CHAR_WRITE_LIERDA2,
    UUID_SERVICE_LIERDA1,
    UUID_SERVICE_LIERDA2,
    UUID_SERVICE_LOGIN,
    UUID_SERVICE_PEILIN,
)
from .protocol import (
    CMD_CLEAR_LIMIT,
    CMD_GET_ANTI_COLLISION,
    CMD_GET_BRIGHTNESS,
    CMD_GET_LED_COLOR,
    CMD_GET_LIGHTING,
    CMD_GET_LOCK,
    CMD_GET_STATUS,
    CMD_GET_VIBRATION,
    CMD_HANDSHAKE,
    CMD_MOVE_DOWN,
    CMD_MOVE_UP,
    CMD_RECALL_MEMORY_1,
    CMD_RECALL_MEMORY_2,
    CMD_RECALL_MEMORY_3,
    CMD_RECALL_MEMORY_4,
    CMD_SAVE_MEMORY_1,
    CMD_SAVE_MEMORY_2,
    CMD_SAVE_MEMORY_3,
    CMD_SAVE_MEMORY_4,
    CMD_STOP,
    DeskState,
    cmd_move_to_height,
    cmd_set_anti_collision,
    cmd_set_brightness,
    cmd_set_led_color,
    cmd_set_lighting,
    cmd_set_lock,
    cmd_set_reminder,
    cmd_set_touch_mode,
    cmd_set_unit,
    cmd_set_vibration,
    parse_notification,
)

_LOGGER = logging.getLogger(__name__)

_RECALL_MEMORY_CMDS: dict[int, bytes] = {
    1: CMD_RECALL_MEMORY_1,
    2: CMD_RECALL_MEMORY_2,
    3: CMD_RECALL_MEMORY_3,
    4: CMD_RECALL_MEMORY_4,
}

_SAVE_MEMORY_CMDS: dict[int, bytes] = {
    1: CMD_SAVE_MEMORY_1,
    2: CMD_SAVE_MEMORY_2,
    3: CMD_SAVE_MEMORY_3,
    4: CMD_SAVE_MEMORY_4,
}


class ControllerVariant(Enum):
    """BLE controller type detected from GATT services."""

    LIERDA1 = auto()  # service ff12
    LIERDA2 = auto()  # service fe60
    PEILIN = auto()  # service 88121427


class DeskyBleClient:
    """Async BLE client for Desky standing desks."""

    def __init__(
        self,
        ble_device: BLEDevice,
        state_callback: Callable[[DeskState], None] | None = None,
    ) -> None:
        self._ble_device = ble_device
        self._client: BleakClient | None = None
        self._variant: ControllerVariant | None = None
        self._write_char: str | None = None
        self._read_char: str | None = None
        self._state = DeskState()
        self._state_callback = state_callback
        self._lock = asyncio.Lock()

    @property
    def state(self) -> DeskState:
        return self._state

    @property
    def variant(self) -> ControllerVariant | None:
        return self._variant

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_connected

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------
    async def connect(self) -> None:
        """Establish BLE connection with retry logic."""
        self._client = await establish_connection(
            BleakClient,
            self._ble_device,
            self._ble_device.address,
        )
        await self._detect_variant()
        await self._setup_notifications()
        await self._send(CMD_HANDSHAKE)
        _LOGGER.info(
            "Connected to Desky %s (variant=%s)",
            self._ble_device.address,
            self._variant,
        )

    async def disconnect(self) -> None:
        if self._client and self._client.is_connected:
            await self._client.disconnect()
        self._client = None

    # ------------------------------------------------------------------
    # Service detection
    # ------------------------------------------------------------------
    async def _detect_variant(self) -> None:
        """Identify the controller variant from advertised GATT services."""
        if self._client is None:
            msg = "Not connected"
            raise RuntimeError(msg)

        service_uuids = {str(s.uuid).lower() for s in self._client.services}

        if UUID_SERVICE_LIERDA2.lower() in service_uuids:
            self._variant = ControllerVariant.LIERDA2
            self._write_char = UUID_CHAR_WRITE_LIERDA2
            self._read_char = UUID_CHAR_READ_LIERDA2
        elif UUID_SERVICE_LIERDA1.lower() in service_uuids:
            self._variant = ControllerVariant.LIERDA1
            self._write_char = UUID_CHAR_WRITE_LIERDA1
            self._read_char = UUID_CHAR_READ_LIERDA1
        elif UUID_SERVICE_PEILIN.lower() in service_uuids:
            self._variant = ControllerVariant.PEILIN
            self._write_char = UUID_CHAR_RW_PEILIN
            self._read_char = UUID_CHAR_RW_PEILIN
        else:
            msg = (
                f"No known Desky service found on {self._ble_device.address}. "
                f"Services: {service_uuids}"
            )
            raise RuntimeError(msg)

        # Peilin requires a login handshake
        if self._variant == ControllerVariant.PEILIN:
            await self._peilin_login(service_uuids)

    async def _peilin_login(self, service_uuids: set[str]) -> None:
        """Send the login payload required by Peilin controllers."""
        if UUID_SERVICE_LOGIN.lower() not in service_uuids:
            _LOGGER.debug("No login service found; skipping Peilin login")
            return
        if self._client is None:
            return
        try:
            await self._client.write_gatt_char(
                UUID_CHAR_LOGIN_WRITE, LOGIN_PAYLOAD, response=True
            )
            _LOGGER.debug("Peilin login handshake sent")
        except Exception:
            _LOGGER.warning("Failed to send Peilin login handshake", exc_info=True)

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------
    async def _setup_notifications(self) -> None:
        if self._client is None or self._read_char is None:
            return
        await self._client.start_notify(self._read_char, self._on_notification)

    def _on_notification(
        self,
        _characteristic: BleakGATTCharacteristic,
        data: bytearray,
    ) -> None:
        if parse_notification(data, self._state) and self._state_callback:
            self._state_callback(self._state)

    # ------------------------------------------------------------------
    # Low-level send
    # ------------------------------------------------------------------
    async def _send(self, frame: bytes) -> None:
        async with self._lock:
            if self._client is None or self._write_char is None:
                msg = "Not connected"
                raise RuntimeError(msg)
            await self._client.write_gatt_char(self._write_char, frame, response=False)
            _LOGGER.debug("TX → %s", frame.hex())

    # ------------------------------------------------------------------
    # High-level desk commands
    # ------------------------------------------------------------------
    async def move_up(self) -> None:
        await self._send(CMD_MOVE_UP)

    async def move_down(self) -> None:
        await self._send(CMD_MOVE_DOWN)

    async def stop(self) -> None:
        await self._send(CMD_STOP)

    async def move_to_height(self, raw_height: int) -> None:
        """Move to a specific height (*raw_height* = cm × 10)."""
        await self._send(CMD_STOP)
        await asyncio.sleep(0.2)
        frame = cmd_move_to_height(raw_height)
        await self._send(frame)

    async def recall_memory(self, slot: int) -> None:
        """Recall a memory preset (slot 1–4)."""
        frame = _RECALL_MEMORY_CMDS.get(slot)
        if frame is None:
            msg = f"Invalid memory slot {slot}"
            raise ValueError(msg)
        await self._send(frame)

    async def save_memory(self, slot: int) -> None:
        """Save current height to a memory slot (1–4)."""
        frame = _SAVE_MEMORY_CMDS.get(slot)
        if frame is None:
            msg = f"Invalid memory slot {slot}"
            raise ValueError(msg)
        await self._send(frame)

    # ------------------------------------------------------------------
    # Status queries
    # ------------------------------------------------------------------
    async def request_status(self) -> None:
        await self._send(CMD_GET_STATUS)

    async def request_all_settings(self) -> None:
        """Query every known setting from the desk."""
        for frame in (
            CMD_GET_ANTI_COLLISION,
            CMD_GET_LOCK,
            CMD_GET_VIBRATION,
            CMD_GET_LED_COLOR,
            CMD_GET_LIGHTING,
            CMD_GET_BRIGHTNESS,
        ):
            await self._send(frame)
            await asyncio.sleep(0.1)

    # ------------------------------------------------------------------
    # Settings setters
    # ------------------------------------------------------------------
    async def set_brightness(self, value: int) -> None:
        await self._send(cmd_set_brightness(value))

    async def set_led_color(self, value: int) -> None:
        await self._send(cmd_set_led_color(value))

    async def set_vibration(self, value: int) -> None:
        await self._send(cmd_set_vibration(value))

    async def set_lock(self, value: int) -> None:
        await self._send(cmd_set_lock(value))

    async def set_lighting(self, value: int) -> None:
        await self._send(cmd_set_lighting(value))

    async def set_anti_collision(self, value: int) -> None:
        await self._send(cmd_set_anti_collision(value))

    async def set_touch_mode(self, value: int) -> None:
        await self._send(cmd_set_touch_mode(value))

    async def set_unit(self, value: int) -> None:
        await self._send(cmd_set_unit(value))

    async def set_reminder(self, minutes: int) -> None:
        await self._send(cmd_set_reminder(minutes))

    async def clear_limits(self) -> None:
        await self._send(CMD_CLEAR_LIMIT)
