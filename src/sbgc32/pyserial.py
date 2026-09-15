"""PySerial transport for the asynchronous SimpleBGC dispatcher."""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import Future
from threading import Event, Lock, Thread
from typing import Any

try:
    import serial
except ImportError:
    serial = None

from .dispatcher import MessageDispatcher
from .protocol import ProtocolCodec

__all__ = ["PySerialTransport"]


class PySerialTransport:
    """Own one COM port and its dedicated receive/transmit threads."""

    def __init__(
        self,
        dispatcher: MessageDispatcher,
        codec: ProtocolCodec,
        *,
        port: str,
        baudrate: int,
        write_timeout: float | None = 1.0,
        serial_factory: Callable[..., Any] | None = None,
    ) -> None:
        if not port:
            raise ValueError("port must not be empty")
        if baudrate <= 0:
            raise ValueError("baudrate must be positive")
        if write_timeout is not None and write_timeout <= 0:
            raise ValueError("write_timeout must be positive or None")

        if serial_factory is None:
            if serial is None:
                raise ImportError("The pyserial backend requires the pyserial dependency.")

            serial_factory = serial.Serial

        self._dispatcher = dispatcher
        self._codec = codec
        self._port_name = port
        self._baudrate = baudrate
        self._write_timeout = write_timeout
        self._serial_factory = serial_factory

        self._serial: Any | None = None
        self._lock = Lock()
        self._started = Event()
        self._stopping = Event()

        self._stop_future: Future[None] | None = None
        self._fatal_error: BaseException | None = None

        self._rx_thread = Thread(
            target=self._rx_loop,
            name="sbgc-rx",
            daemon=True,
        )
        self._tx_thread = Thread(
            target=self._tx_loop,
            name="sbgc-tx",
            daemon=True,
        )

    @property
    def fatal_error(self) -> BaseException | None:
        """Emergency stop of COM port."""

        with self._lock:
            return self._fatal_error

    def _fail_transport(self, error: BaseException) -> None:
        """Record the first I/O failure and fail all outstanding requests."""

        with self._lock:
            if self._fatal_error is not None:
                return
            self._fatal_error = error

        self.stop()

    def start(self) -> None:
        """Open the port and start RX/TX threads.

        Start the dispatcher and WorkerManager before calling this method.
        """

        if self._started.is_set():
            raise RuntimeError("PySerialTransport is already started")

        try:
            opened_port = self._serial_factory(
                port=self._port_name,
                baudrate=self._baudrate,
                timeout=None,
                write_timeout=self._write_timeout,
            )
        except BaseException as error:
            with self._lock:
                self._fatal_error = error
            raise ConnectionError(f"Cannot open serial port {self._port_name!r}") from error

        with self._lock:
            self._serial = opened_port

        self._started.set()
        self._rx_thread.start()
        self._tx_thread.start()

    def stop(self) -> Future[None]:
        """Request shutdown without waiting for RX/TX threads.

        The dispatcher completes every pending request with an error and
        places stop markers into the TX and worker queues.
        """

        with self._lock:
            if self._stop_future is not None:
                return self._stop_future

            self._stopping.set()
            self._stop_future = self._dispatcher.stop()

        self._interrupt_port()
        return self._stop_future

    close = stop

    def join(self, timeout: float | None = None) -> None:
        """Wait for the physical I/O threads to finish."""

        if not self._started.is_set():
            return

        self._rx_thread.join(timeout)
        self._tx_thread.join(timeout)

    def _rx_loop(self) -> None:
        """Wait for COM bytes, parse them through the C codec, notify dispatcher."""

        try:
            port = self._require_port()

            while not self._stopping.is_set():
                first_byte = port.read(1)

                if self._stopping.is_set():
                    return
                if not first_byte:
                    raise ConnectionError("Serial port was closed while reading")

                # ``in_waiting`` is only a snapshot.  It prevents an extra
                # blocking read when this packet already arrived in the OS buffer.
                available = port.in_waiting
                rest = port.read(available) if available else b""

                for frame in self._codec.feed(first_byte + rest):
                    self._dispatcher.submit_incoming(frame)

        except BaseException as error:
            if not self._stopping.is_set():
                self._fail_transport(error)

    def _tx_loop(self) -> None:
        """Wait for dispatcher commands, encode and write complete wire frames."""

        try:
            while True:
                command = self._dispatcher.take_outgoing()

                # Dispatcher sends None as a queue sentinel during shutdown.
                if command is None or self._stopping.is_set():
                    return

                try:
                    self._write_all(self._codec.encode(command.command_id, command.payload))
                except BaseException as error:
                    if self._stopping.is_set():
                        return

                    self._dispatcher.submit_transmit_failed(
                        command.generation,
                        error,
                    )
                    self._fail_transport(error)
                    return

                # A request timeout starts only after a full serial.write().
                self._dispatcher.submit_transmitted(command.generation)

        except BaseException as error:
            if not self._stopping.is_set():
                self._fail_transport(error)

    def _write_all(self, data: bytes) -> None:
        """Write all bytes, also when a driver accepts a partial write."""

        port = self._require_port()
        offset = 0

        while offset < len(data):
            written = port.write(data[offset:])
            if written is None or written <= 0:
                raise ConnectionError("Serial driver accepted zero bytes")
            offset += written

    def _interrupt_port(self) -> None:
        """Wake blocked PySerial calls without delays or polling."""

        with self._lock:
            port = self._serial

        if port is None:
            return

        try:
            port.cancel_read()
        except (AttributeError, OSError):
            pass

        try:
            port.cancel_write()
        except (AttributeError, OSError):
            pass

        try:
            port.close()
        except OSError:
            pass

    def _require_port(self) -> Any:
        with self._lock:
            if self._serial is None:
                raise RuntimeError("Serial port is not open")
            return self._serial
