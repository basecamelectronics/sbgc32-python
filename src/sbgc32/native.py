from __future__ import annotations

import ctypes
import struct
import sys
from collections import deque
from enum import IntEnum
from pathlib import Path
from time import monotonic_ns, sleep
from threading import Event, Lock, Thread
from typing import Any


class NativeError(RuntimeError):
    """Error returned by the native SimpleBGC bridge."""


class NativeStatus(IntEnum):
    OK = 0
    ERROR = -1
    INVALID_ARGUMENT = -2
    NOT_CONNECTED = -3
    OPEN_FAILED = -4
    COMMUNICATION_ERROR = -5
    MODULE_DISABLED = -6


class NativeAxis3(ctypes.Structure):
    _fields_ = [
        ("roll", ctypes.c_float),
        ("pitch", ctypes.c_float),
        ("yaw", ctypes.c_float),
    ]


class NativeAngles(ctypes.Structure):
    _fields_ = [
        ("imu", NativeAxis3),
        ("target", NativeAxis3),
        ("target_speed", NativeAxis3),
    ]


class NativeAxisGAE(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("imu_angle", ctypes.c_int16),
        ("target_angle", ctypes.c_int16),
        ("frame_cam_angle", ctypes.c_int32),
        ("reserved", ctypes.c_uint8 * 10),
    ]


class NativeAnglesExt(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("axis_gae", NativeAxisGAE * 3),
    ]


class NativeScriptDebugInfo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("current_command_counter", ctypes.c_uint16),
        ("error_code", ctypes.c_uint8),
    ]


class NativeAxisRealtimeData(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("acc_data", ctypes.c_int16),
        ("gyro_data", ctypes.c_int16),
    ]


class NativeRealtimeData(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("axis_rtd", NativeAxisRealtimeData * 3),
        ("serial_error_count", ctypes.c_uint16),
        ("system_error", ctypes.c_uint16),
        ("system_sub_error", ctypes.c_uint8),
        ("reserved", ctypes.c_uint8 * 3),
        ("rc_roll", ctypes.c_int16),
        ("rc_pitch", ctypes.c_int16),
        ("rc_yaw", ctypes.c_int16),
        ("rc_cmd", ctypes.c_int16),
        ("ext_fc_roll", ctypes.c_int16),
        ("ext_fc_pitch", ctypes.c_int16),
        ("imu_angle", ctypes.c_int16 * 3),
        ("frame_imu_angle", ctypes.c_int16 * 3),
        ("target_angle", ctypes.c_int16 * 3),
        ("cycle_time", ctypes.c_uint16),
        ("i2c_error_count", ctypes.c_uint16),
        ("error_code", ctypes.c_uint8),
        ("bat_level", ctypes.c_uint16),
        ("rt_data_flags", ctypes.c_uint8),
        ("cur_imu", ctypes.c_uint8),
        ("cur_profile", ctypes.c_uint8),
        ("motor_power", ctypes.c_uint8 * 3),
        ("frame_cam_angle", ctypes.c_int16 * 3),
        ("reserved1", ctypes.c_uint8),
        ("balance_error", ctypes.c_int16 * 3),
        ("current", ctypes.c_uint16),
        ("mag_data", ctypes.c_int16 * 3),
        ("imu_temperature", ctypes.c_int8),
        ("frame_imu_temperature", ctypes.c_int8),
        ("imu_g_error", ctypes.c_uint8),
        ("imu_h_error", ctypes.c_uint8),
        ("motor_out", ctypes.c_int16 * 3),
        ("calib_mode", ctypes.c_uint8),
        ("can_imu_ext_sens_error", ctypes.c_uint8),
        ("actual_angle", ctypes.c_int16 * 3),
        ("system_state_flags", ctypes.c_uint32),
        ("reserved2", ctypes.c_uint8 * 18),
    ]


class NativeBoardInfo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("board_ver", ctypes.c_uint8),
        ("firmware_ver", ctypes.c_uint16),
        ("state_flags", ctypes.c_uint8),
        ("board_features", ctypes.c_uint16),
        ("connection_flag", ctypes.c_uint8),
        ("firmware_extra_id", ctypes.c_uint32),
        ("board_features_ext", ctypes.c_uint16),
        ("main_imu_sensor_model", ctypes.c_uint8),
        ("frame_imu_sensor_model", ctypes.c_uint8),
        ("build_number", ctypes.c_uint8),
        ("base_firmware_ver", ctypes.c_uint16),
    ]

class NativeBoardInfo3(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("device_id", ctypes.c_uint8 * 9),
        ("mcu_id", ctypes.c_uint8 * 12),
        ("eeprom_size", ctypes.c_uint32),

        ("script_slot_1_size", ctypes.c_uint16),
        ("script_slot_2_size", ctypes.c_uint16),
        ("script_slot_3_size", ctypes.c_uint16),
        ("script_slot_4_size", ctypes.c_uint16),
        ("script_slot_5_size", ctypes.c_uint16),

        ("profile_set_slots", ctypes.c_uint8),
        ("profile_set_current", ctypes.c_uint8),
        ("flash_size", ctypes.c_uint8),
        ("imu_calib_info", ctypes.c_uint8 * 2),

        ("script_slot_6_size", ctypes.c_uint16),
        ("script_slot_7_size", ctypes.c_uint16),
        ("script_slot_8_size", ctypes.c_uint16),
        ("script_slot_9_size", ctypes.c_uint16),
        ("script_slot_10_size", ctypes.c_uint16),

        ("hardware_flags", ctypes.c_uint16),
        ("board_features_ext2", ctypes.c_uint32),
        ("can_driver_main_limit", ctypes.c_uint8),
        ("can_driver_aux_limit", ctypes.c_uint8),
        ("adjustable_variables_total", ctypes.c_uint8),
    ]


TxCallback = ctypes.CFUNCTYPE(
    ctypes.c_uint8,
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_uint8),
    ctypes.c_uint16,
)

RxCallback = ctypes.CFUNCTYPE(ctypes.c_uint8, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint8))
AvailableCallback = ctypes.CFUNCTYPE(ctypes.c_uint16, ctypes.c_void_p)
TimeCallback = ctypes.CFUNCTYPE(ctypes.c_uint32, ctypes.c_void_p)


class _PySerialTransport:
    """Synchronous serial transport used by the native Serial API callbacks."""

    def __init__(self, port: str, baudrate: int) -> None:
        try:
            import serial
        except ImportError as error:
            raise NativeError("pyserial is required to communicate with a SimpleBGC controller.") from error

        self._serial_module = serial
        self._port = port
        self._baudrate = baudrate
        self._buffer: deque[int] = deque()
        self._buffer_lock = Lock()
        self._open()

    def _open(self) -> None:
        self._serial: Any = self._serial_module.Serial(
            self._port,
            self._baudrate,
            timeout=0.1,
            write_timeout=1,
        )
        self._stop_reader = Event()
        self._serial.reset_input_buffer()
        self._reader = Thread(target=self._read_loop, name="sbgc32-serial-reader", daemon=True)
        self._reader.start()

    def _read_loop(self) -> None:
        while not self._stop_reader.is_set():
            try:
                data = self._serial.read(self._serial.in_waiting or 1)
            except Exception:
                return
            if data:
                with self._buffer_lock:
                    self._buffer.extend(data)

    def write(self, data: bytes) -> bool:
        try:
            if self._serial.write(data) != len(data):
                return False
            self._serial.flush()
            return True
        except Exception:
            return False

    def read_byte(self) -> int | None:
        with self._buffer_lock:
            return self._buffer.popleft() if self._buffer else None

    def available(self) -> int:
        with self._buffer_lock:
            return min(len(self._buffer), 0xFFFE)

    def recover(self) -> None:
        self.close()
        with self._buffer_lock:
            self._buffer.clear()
        self._open()

    def close(self) -> None:
        self._stop_reader.set()
        try:
            self._serial.cancel_read()
        except Exception:
            pass
        self._reader.join(timeout=1)
        if self._serial.is_open:
            self._serial.close()

    def request(self, command_id: int, payload: bytes = b"", timeout: float = 0.3) -> bytes | None:
        """Send a SimpleBGC v2 command and return its validated payload."""
        header = bytes((command_id, len(payload), (command_id + len(payload)) & 0xFF))
        frame = b"\x24" + header + payload + struct.pack("<H", _crc16(header + payload))

        with self._buffer_lock:
            self._buffer.clear()
        if not self.write(frame):
            return None

        deadline = monotonic_ns() + int(timeout * 1_000_000_000)
        while monotonic_ns() < deadline:
            with self._buffer_lock:
                while self._buffer and self._buffer[0] != 0x24:
                    self._buffer.popleft()
                if len(self._buffer) >= 4:
                    packet_size = 6 + self._buffer[2]
                    if len(self._buffer) >= packet_size:
                        packet = bytes(self._buffer.popleft() for _ in range(packet_size))
                        response_id, payload_size, header_checksum = packet[1:4]
                        response_payload = packet[4:-2]
                        expected_crc = struct.unpack("<H", packet[-2:])[0]
                        if (
                            response_id == command_id
                            and payload_size == len(response_payload)
                            and header_checksum == (response_id + payload_size) & 0xFF
                            and expected_crc == _crc16(packet[1:-2])
                        ):
                            return response_payload
            sleep(0.001)
        return None

    def wait_for_command(self, command_id: int, timeout: float) -> bytes | None:
        """Wait for a validated unsolicited SimpleBGC v2 command packet."""
        deadline = monotonic_ns() + int(timeout * 1_000_000_000)
        while monotonic_ns() < deadline:
            with self._buffer_lock:
                while self._buffer and self._buffer[0] != 0x24:
                    self._buffer.popleft()
                if len(self._buffer) >= 4:
                    packet_size = 6 + self._buffer[2]
                    if len(self._buffer) >= packet_size:
                        packet = bytes(self._buffer.popleft() for _ in range(packet_size))
                        received_id, payload_size, header_checksum = packet[1:4]
                        received_payload = packet[4:-2]
                        expected_crc = struct.unpack("<H", packet[-2:])[0]
                        if (
                            received_id == command_id
                            and payload_size == len(received_payload)
                            and header_checksum == (received_id + payload_size) & 0xFF
                            and expected_crc == _crc16(packet[1:-2])
                        ):
                            return received_payload
            sleep(0.001)
        return None


def _crc16(data: bytes) -> int:
    """SimpleBGC v2 CRC-16"""
    value = 0
    for byte in data:
        for mask in (1, 2, 4, 8, 16, 32, 64, 128):
            data_bit = bool(byte & mask)
            crc_bit = bool(value & 0x8000)
            value = (value << 1) & 0xFFFF
            if data_bit != crc_bit:
                value ^= 0x8005
    return value


def _transport_from_context(context: int) -> _PySerialTransport:
    reference = ctypes.cast(context, ctypes.POINTER(ctypes.py_object))
    return reference.contents.value


@TxCallback
def _serial_transmit(context: int, data: ctypes.POINTER(ctypes.c_uint8), size: int) -> int:
    try:
        return 0 if _transport_from_context(context).write(ctypes.string_at(data, size)) else 1
    except Exception:
        return 1


@RxCallback
def _serial_receive_byte(context: int, data: ctypes.POINTER(ctypes.c_uint8)) -> int:
    try:
        value = _transport_from_context(context).read_byte()
        if value is None:
            return 1
        data[0] = value
        return 0
    except Exception:
        return 1


@AvailableCallback
def _serial_available_bytes(context: int) -> int:
    try:
        return _transport_from_context(context).available()
    except Exception:
        return 0


@TimeCallback
def _serial_time_ms(context: int) -> int:
    del context
    return (monotonic_ns() // 1_000_000) & 0xFFFFFFFF


def _library_name() -> str:
    if sys.platform == "win32":
        return "sbgc_python.dll"
    if sys.platform == "darwin":
        return "libsbgc_python.dylib"
    return "libsbgc_python.so"


class NativeLibrary:

    def __init__(self, library_path: str | Path | None = None) -> None:
        if library_path is None:
            library_path = Path(__file__).parent / "_native" / _library_name()

        try:
            self._library = ctypes.CDLL(str(library_path))
        except OSError as error:
            raise NativeError(
                f"Native SimpleBGC library was not found at {library_path}. "
                "Build it with CMake before using the package."
            ) from error

        self._configure_functions()
        self._transports: dict[int, _PySerialTransport] = {}
        self._contexts: dict[int, ctypes.py_object] = {}
        self._raw_angle_devices: set[int] = set()
        self._raw_board_info_devices: set[int] = set()
        self._raw_board_info_3_devices: set[int] = set()
        self._raw_angle_ext_devices: set[int] = set()
        self._raw_reset_devices: set[int] = set()
        self._raw_script_debug_devices: set[int] = set()
        self._raw_realtime_data_3_devices: set[int] = set()
        self._raw_realtime_data_4_devices: set[int] = set()
        self._raw_realtime_data_custom_devices: set[int] = set()

    def _configure_functions(self) -> None:
        lib = self._library
        lib.sbgc_py_open_com.argtypes = [ctypes.c_char_p, ctypes.c_uint32]
        lib.sbgc_py_open_com.restype = ctypes.c_void_p
        lib.sbgc_py_open.argtypes = [
            ctypes.c_void_p,
            TxCallback,
            RxCallback,
            AvailableCallback,
            TimeCallback,
        ]
        lib.sbgc_py_open.restype = ctypes.c_void_p
        lib.sbgc_py_close.argtypes = [ctypes.c_void_p]
        lib.sbgc_py_close.restype = None
        lib.sbgc_py_recover.argtypes = [ctypes.c_void_p]
        lib.sbgc_py_recover.restype = ctypes.c_int

        lib.sbgc_py_get_angles.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAngles)
        ]
        lib.sbgc_py_get_angles.restype = ctypes.c_int

        lib.sbgc_py_get_angles_ext.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeAnglesExt)
        ]
        lib.sbgc_py_get_angles_ext.restype = ctypes.c_int

        lib.sbgc_py_get_board_info.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeBoardInfo),
        ]
        lib.sbgc_py_get_board_info.restype = ctypes.c_int

        lib.sbgc_py_get_board_info_3.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeBoardInfo3),
        ]
        lib.sbgc_py_get_board_info_3.restype = ctypes.c_int

        lib.sbgc_py_reset.argtypes = [ctypes.c_void_p, ctypes.c_uint8, ctypes.c_uint16]
        lib.sbgc_py_reset.restype = ctypes.c_int
        lib.sbgc_py_expect_reset.argtypes = [ctypes.c_void_p]
        lib.sbgc_py_expect_reset.restype = ctypes.c_int
        lib.sbgc_py_motors_on.argtypes = [ctypes.c_void_p]
        lib.sbgc_py_motors_on.restype = ctypes.c_int
        lib.sbgc_py_motors_off.argtypes = [ctypes.c_void_p, ctypes.c_uint8]
        lib.sbgc_py_motors_off.restype = ctypes.c_int
        lib.sbgc_py_run_script.argtypes = [ctypes.c_void_p, ctypes.c_uint8, ctypes.c_uint8]
        lib.sbgc_py_run_script.restype = ctypes.c_int
        lib.sbgc_py_read_script_debug_info.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeScriptDebugInfo),
        ]
        lib.sbgc_py_read_script_debug_info.restype = ctypes.c_int
        lib.sbgc_py_get_realtime_data_3.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeRealtimeData),
        ]
        lib.sbgc_py_get_realtime_data_3.restype = ctypes.c_int
        lib.sbgc_py_get_realtime_data_4.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(NativeRealtimeData),
        ]
        lib.sbgc_py_get_realtime_data_4.restype = ctypes.c_int
        lib.sbgc_py_get_realtime_data_custom.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint8),
            ctypes.c_uint8,
        ]
        lib.sbgc_py_get_realtime_data_custom.restype = ctypes.c_int

        lib.sbgc_py_copy_last_tx.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint16]
        lib.sbgc_py_copy_last_tx.restype = ctypes.c_uint16
        lib.sbgc_py_copy_last_rx.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint16]
        lib.sbgc_py_copy_last_rx.restype = ctypes.c_uint16

    def open(self, port: str, baudrate: int) -> int:
        transport = _PySerialTransport(port, baudrate)
        context = ctypes.py_object(transport)
        context_pointer = ctypes.cast(ctypes.pointer(context), ctypes.c_void_p)
        handle = self._library.sbgc_py_open(
            context_pointer,
            _serial_transmit,
            _serial_receive_byte,
            _serial_available_bytes,
            _serial_time_ms,
        )
        if not handle:
            transport.close()
            raise NativeError(f"Cannot open {port} at {baudrate} baud.")
        device = int(handle)
        self._transports[device] = transport
        self._contexts[device] = context
        return device

    def close(self, device: int) -> None:
        try:
            self._library.sbgc_py_close(device)
        finally:
            transport = self._transports.pop(device, None)
            self._contexts.pop(device, None)
            self._raw_angle_devices.discard(device)
            self._raw_angle_ext_devices.discard(device)
            self._raw_board_info_devices.discard(device)
            self._raw_board_info_3_devices.discard(device)
            self._raw_reset_devices.discard(device)
            self._raw_script_debug_devices.discard(device)
            self._raw_realtime_data_3_devices.discard(device)
            self._raw_realtime_data_4_devices.discard(device)
            self._raw_realtime_data_custom_devices.discard(device)
            if transport is not None:
                transport.close()

    def recover(self, device: int) -> None:
        self._transports[device].recover()
        status = self._library.sbgc_py_recover(device)
        if status != NativeStatus.OK:
            raise NativeError(f"Cannot recover the SimpleBGC connection (native status {status}).")
        self._raw_angle_devices.discard(device)
        self._raw_angle_ext_devices.discard(device)
        self._raw_board_info_devices.discard(device)
        self._raw_board_info_3_devices.discard(device)
        self._raw_script_debug_devices.discard(device)
        self._raw_realtime_data_3_devices.discard(device)
        self._raw_realtime_data_4_devices.discard(device)
        self._raw_realtime_data_custom_devices.discard(device)

    def reset(self, device: int, flags: int, delay_ms: int) -> None:
        status = self._library.sbgc_py_reset(device, flags, delay_ms)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "RESET is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"RESET transmission failed with native status {status}. "
            f"Last exchange: {self.last_exchange(device)}"
        )

    def expect_reset(self, device: int, timeout: float) -> None:
        if device in self._raw_reset_devices:
            if self._transports[device].wait_for_command(0x72, timeout) is not None:
                return
            raise NativeError("RESET confirmation was not received in direct serial fallback mode.")

        status = self._library.sbgc_py_expect_reset(device)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "RESET confirmation is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        self._raw_reset_devices.add(device)
        if self._transports[device].wait_for_command(0x72, timeout) is not None:
            return
        raise NativeError(
            f"RESET confirmation was not received (native status {status}). "
            f"Last exchange: {self.last_exchange(device)}"
        )

    def motors_on(self, device: int) -> None:
        status = self._library.sbgc_py_motors_on(device)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "MOTORS_ON is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"MOTORS_ON failed with native status {status}. "
            f"Last exchange: {self.last_exchange(device)}"
        )

    def motors_off(self, device: int, mode: int) -> None:
        status = self._library.sbgc_py_motors_off(device, mode)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "MOTORS_OFF is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"MOTORS_OFF failed with native status {status}. "
            f"Last exchange: {self.last_exchange(device)}"
        )

    def run_script(self, device: int, mode: int, slot: int) -> None:
        status = self._library.sbgc_py_run_script(device, mode, slot)
        if status == NativeStatus.OK:
            return
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "RUN_SCRIPT is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )
        raise NativeError(
            f"RUN_SCRIPT failed with native status {status}. "
            f"Last exchange: {self.last_exchange(device)}"
        )

    def read_script_debug_info(self, device: int, timeout: float) -> NativeScriptDebugInfo:
        if device in self._raw_script_debug_devices:
            result = self._read_script_debug_info_raw(device, timeout)
            if result is not None:
                return result
            raise NativeError("SCRIPT_DEBUG was not received in direct serial fallback mode.")

        result = NativeScriptDebugInfo()
        status = self._library.sbgc_py_read_script_debug_info(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "SCRIPT_DEBUG is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        self._raw_script_debug_devices.add(device)
        result = self._read_script_debug_info_raw(device, timeout)
        if result is not None:
            return result
        raise NativeError(
            f"SCRIPT_DEBUG was not received (native status {status}). "
            f"Last exchange: {self.last_exchange(device)}"
        )

    def _read_script_debug_info_raw(self, device: int, timeout: float) -> NativeScriptDebugInfo | None:
        payload = self._transports[device].wait_for_command(0x3A, timeout)
        if payload is None or len(payload) != 3:
            return None
        return NativeScriptDebugInfo.from_buffer_copy(payload)

    def get_realtime_data_3(self, device: int) -> NativeRealtimeData:
        return self._get_realtime_data(device, 3)

    def get_realtime_data_4(self, device: int) -> NativeRealtimeData:
        return self._get_realtime_data(device, 4)

    def get_realtime_data(self, device: int) -> NativeRealtimeData:
        return self.get_realtime_data_3()

    def get_realtime_data_custom(self, device: int, flags: int, payload_size: int) -> bytes:
        if not 2 <= payload_size <= 0xFF:
            raise ValueError("payload_size must be in range 2..255")
        if device in self._raw_realtime_data_custom_devices:
            return self._get_realtime_data_custom_raw(device, flags, payload_size)

        result = (ctypes.c_uint8 * (payload_size + 4))()
        status = self._library.sbgc_py_get_realtime_data_custom(
            device, flags, result, payload_size
        )
        if status == NativeStatus.OK:
            return bytes(result[4:])
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "REALTIME_DATA_CUSTOM is unavailable: SBGC_REALTIME_MODULE is "
                "disabled in serialAPI_Config.h."
            )

        self.recover(device)
        try:
            value = self._get_realtime_data_custom_raw(device, flags, payload_size)
        except NativeError:
            raise NativeError(
                f"REALTIME_DATA_CUSTOM failed with native status {status}. "
                f"Last exchange: {self.last_exchange(device)}"
            ) from None
        self._raw_realtime_data_custom_devices.add(device)
        return value

    def _get_realtime_data_custom_raw(
        self, device: int, flags: int, payload_size: int
    ) -> bytes:
        payload = self._transports[device].request(
            0x58, struct.pack("<I", flags) + b"\x00" * 6
        )
        if payload is None or len(payload) != payload_size:
            received_size = "-" if payload is None else str(len(payload))
            raise NativeError(
                "REALTIME_DATA_CUSTOM direct serial fallback received "
                f"{received_size} bytes; expected {payload_size}."
            )
        return payload

    def _get_realtime_data(self, device: int, version: int) -> NativeRealtimeData:
        raw_devices = (
            self._raw_realtime_data_3_devices
            if version == 3
            else self._raw_realtime_data_4_devices
        )
        command_id = 0x17 if version == 3 else 0x19
        payload_size = 63 if version == 3 else 124
        if device in raw_devices:
            result = self._get_realtime_data_raw(device, command_id, payload_size)
            if result is not None:
                return result
            raise NativeError(f"REALTIME_DATA_{version} failed in direct serial fallback mode.")

        result = NativeRealtimeData()
        function = (
            self._library.sbgc_py_get_realtime_data_3
            if version == 3
            else self._library.sbgc_py_get_realtime_data_4
        )
        status = function(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                f"REALTIME_DATA_{version} is unavailable: SBGC_REALTIME_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        self.recover(device)
        result = self._get_realtime_data_raw(device, command_id, payload_size)
        if result is not None:
            raw_devices.add(device)
            return result
        raise NativeError(
            f"REALTIME_DATA_{version} failed in Serial API and direct serial fallback mode "
            f"with native status {status}. Last exchange: {self.last_exchange(device)}"
        )

    def _get_realtime_data_raw(
        self, device: int, command_id: int, payload_size: int
    ) -> NativeRealtimeData | None:
        payload = self._transports[device].request(command_id)
        if payload is None or len(payload) != payload_size:
            return None
        return NativeRealtimeData.from_buffer_copy(
            payload + b"\x00" * (ctypes.sizeof(NativeRealtimeData) - len(payload))
        )


    def get_angles(self, device: int) -> NativeAngles:
        if device in self._raw_angle_devices:
            result = self._get_angles_raw(device)
            if result is not None:
                return result
            raise NativeError("GET_ANGLES failed in direct serial fallback mode.")

        status = NativeStatus.ERROR
        result = NativeAngles()
        status = self._library.sbgc_py_get_angles(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_ANGLES is unavailable: SBGC_REALTIME_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        self.recover(device)
        result = self._get_angles_raw(device)
        if result is not None:
            self._raw_angle_devices.add(device)
            return result

        raise NativeError(
            "GET_ANGLES failed in Serial API and direct serial fallback mode with native status "
            f"{status}. Last exchange: {self.last_exchange(device)}"
        )

    def _get_angles_raw(self, device: int) -> NativeAngles | None:
        payload = self._transports[device].request(0x49)
        if payload is None or len(payload) != 18:
            return None

        values = struct.unpack("<9h", payload)
        axes = [values[offset : offset + 3] for offset in range(0, 9, 3)]
        angle_scale = 360.0 / 16384.0
        speed_scale = 0.1220740379
        return NativeAngles(
            imu=NativeAxis3(*(axis[0] * angle_scale for axis in axes)),
            target=NativeAxis3(*(axis[1] * angle_scale for axis in axes)),
            target_speed=NativeAxis3(*(axis[2] * speed_scale for axis in axes)),
        )


    def get_angles_ext(self, device: int) -> NativeAnglesExt:
        if device in self._raw_angle_ext_devices:
            result = self._get_angles_ext_raw(device)
            if result is not None:
                return result
            raise NativeError("GET_ANGLES_EXT failed in direct serial fallback mode.")

        status = NativeStatus.ERROR
        result = NativeAnglesExt()
        status = self._library.sbgc_py_get_angles_ext(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_ANGLES_EXT is unavailable: SBGC_REALTIME_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        self.recover(device)
        result = self._get_angles_ext_raw(device)
        if result is not None:
            self._raw_angle_ext_devices.add(device)
            return result

        raise NativeError(
            "GET_ANGLES_EXT failed in Serial API and direct serial fallback mode with native status "
            f"{status}. Last exchange: {self.last_exchange(device)}"
        )

    def _get_angles_ext_raw(self, device: int) -> NativeAnglesExt | None:
        payload = self._transports[device].request(0x3D)
        if payload is None or len(payload) != 54:
            return None
        return NativeAnglesExt.from_buffer_copy(payload)


    def get_board_info(self, device: int) -> NativeBoardInfo:
        if device in self._raw_board_info_devices:
            result = self._get_board_info_raw(device)
            if result is not None:
                return result
            raise NativeError("GET_BOARD_INFO failed in direct serial fallback mode.")

        result = NativeBoardInfo()
        status = self._library.sbgc_py_get_board_info(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_BOARD_INFO is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        self.recover(device)
        result = self._get_board_info_raw(device)
        if result is not None:
            self._raw_board_info_devices.add(device)
            return result

        raise NativeError(
            "GET_BOARD_INFO failed in Serial API and direct serial fallback mode with native status "
            f"{status}. Last exchange: {self.last_exchange(device)}"
        )

    def _get_board_info_raw(self, device: int) -> NativeBoardInfo | None:
        payload = self._transports[device].request(0x56, b"\x00\x00")
        if payload is None or len(payload) != 18:
            return None

        (
            board_ver,
            firmware_ver,
            state_flags,
            board_features,
            connection_flag,
            firmware_extra_id,
            board_features_ext,
            main_imu_sensor_model,
            frame_imu_sensor_model,
            build_number,
            base_firmware_ver,
        ) = struct.unpack("<BHBHBIHBBBH", payload)
        if board_ver == 0 or firmware_ver == 0:
            return None
        return NativeBoardInfo(
            board_ver=board_ver,
            firmware_ver=firmware_ver,
            state_flags=state_flags,
            board_features=board_features,
            connection_flag=connection_flag,
            firmware_extra_id=firmware_extra_id,
            board_features_ext=board_features_ext,
            main_imu_sensor_model=main_imu_sensor_model,
            frame_imu_sensor_model=frame_imu_sensor_model,
            build_number=build_number,
            base_firmware_ver=base_firmware_ver,
        )


    def get_board_info_3(self, device: int) -> NativeBoardInfo3:
        if device in self._raw_board_info_3_devices:
            result = self._get_board_info_3_raw(device)
            if result is not None:
                return result
            raise NativeError("GET_BOARD_INFO_3 failed in direct serial fallback mode.")

        result = NativeBoardInfo3()
        status = self._library.sbgc_py_get_board_info_3(device, ctypes.byref(result))
        if status == NativeStatus.OK:
            return result
        if status == NativeStatus.MODULE_DISABLED:
            raise NativeError(
                "GET_BOARD_INFO_3 is unavailable: SBGC_SERVICE_MODULE is disabled "
                "in serialAPI_Config.h."
            )

        self.recover(device)
        result = self._get_board_info_3_raw(device)
        if result is not None:
            self._raw_board_info_3_devices.add(device)
            return result

        raise NativeError(
            "GET_BOARD_INFO_3 failed in Serial API and direct serial fallback mode "
            f"with native status {status}. Last exchange: {self.last_exchange(device)}"
        )

    def _get_board_info_3_raw(self, device: int) -> NativeBoardInfo3 | None:
        payload = self._transports[device].request(0x14)
        if payload is None or len(payload) != 69:
            return None
        return NativeBoardInfo3.from_buffer_copy(payload)

    def last_exchange(self, device: int) -> str:
        def read(function: object) -> bytes:
            buffer = (ctypes.c_uint8 * 256)()
            size = function(device, buffer, len(buffer))
            return bytes(buffer[:size])

        tx = read(self._library.sbgc_py_copy_last_tx)
        rx = read(self._library.sbgc_py_copy_last_rx)
        return f"TX={tx.hex(' ') or '-'}; RX={rx.hex(' ') or '-'}"
