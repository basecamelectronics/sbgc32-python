from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable, Hashable
from concurrent.futures import Future
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from queue import Empty, Queue
from threading import Event, Lock, Thread
from time import monotonic
from typing import Any

from .protocol import WireFrame

ResponseKey = Hashable
Decoder = Callable[[WireFrame], Any]
KeyExtractor = Callable[[WireFrame], ResponseKey | None]


class CommandTimeoutError(TimeoutError):
    """The board did not response."""
    pass


@dataclass(frozen=True, slots=True)
class OutgoingCommand:
    """Command go into TX thread."""

    generation: int
    command_id: int
    payload: bytes


@dataclass(frozen=True, slots=True)
class ReceivedFrame:
    """Command go into RX thread."""

    arrival_generation: int
    request_generation: int | None
    response_key: ResponseKey | None
    wire: WireFrame


_BODE_SUBSCRIPTION_CLOSED = object()


class BodeSubscription:
    """Exclusive receiver for one active Bode-test data stream."""

    def __init__(self, dispatcher: "MessageDispatcher", generation: int) -> None:
        self._dispatcher = dispatcher
        self.generation = generation
        self._frames: Queue[ReceivedFrame | object] = Queue()
        self._closed = Event()

    @property
    def closed(self) -> bool:
        """Whether this subscription can no longer receive packets."""

        return self._closed.is_set()

    def get(self, timeout: float | None = None) -> ReceivedFrame:
        """Wait for the next Bode packet or raise if the subscription closes."""

        frame = self._frames.get(timeout=timeout)
        if frame is _BODE_SUBSCRIPTION_CLOSED:
            self._frames.put(_BODE_SUBSCRIPTION_CLOSED)
            raise ConnectionError("Bode-test subscription is closed")
        return frame

    def close(self) -> None:
        """Stop receiving packets and release the exclusive Bode session."""

        if self._close_locally():
            self._dispatcher.close_bode_subscription(self.generation)

    def _submit(self, frame: ReceivedFrame) -> None:
        if not self.closed:
            self._frames.put(frame)

    def _close_locally(self) -> bool:
        if self._closed.is_set():
            return False
        self._closed.set()
        self._frames.put(_BODE_SUBSCRIPTION_CLOSED)
        return True


@dataclass(frozen=True, slots=True)
class CompletionJob:
    """Give a job to the worker. It will complite Future."""

    route: str
    future: Future[Any]
    received: ReceivedFrame | None
    decoder: Decoder | None
    error: BaseException | None


@dataclass(slots=True)
class _PendingRequest:
    generation: int
    command_id: int
    payload: bytes
    response_key: ResponseKey
    timeout: float | None
    route: str
    decoder: Decoder
    future: Future[Any]
    complete_on_transmit: bool = False
    dispatched: bool = False
    transmitted: bool = False
    deadline: float | None = None


@dataclass(frozen=True, slots=True)
class _SubmitRequest:
    command_id: int
    payload: bytes
    response_command_id: int
    response_key: ResponseKey
    timeout: float | None
    route: str
    decoder: Decoder
    future: Future[Any]
    complete_on_transmit: bool = False


@dataclass(frozen=True, slots=True)
class _IncomingFrame:
    frame: WireFrame


@dataclass(frozen=True, slots=True)
class _AwaitUnsolicited:
    command_id: int
    timeout: float | None
    route: str
    decoder: Decoder
    future: Future[Any]


@dataclass(frozen=True, slots=True)
class _OpenBodeSubscription:
    future: Future[BodeSubscription]


@dataclass(frozen=True, slots=True)
class _CloseBodeSubscription:
    generation: int


@dataclass(slots=True)
class _UnsolicitedWaiter:
    generation: int
    command_id: int
    timeout: float | None
    route: str
    decoder: Decoder
    future: Future[Any]
    deadline: float | None = None


@dataclass(frozen=True, slots=True)
class _Transmitted:
    generation: int


@dataclass(frozen=True, slots=True)
class _TransmitFailed:
    generation: int
    error: BaseException


@dataclass(frozen=True, slots=True)
class _Stop:
    completed: Future[None]


class MessageDispatcher:
    """Dispatcher for one phisical port."""

    CMD_CONFIRM = 67
    CMD_ERROR = 255

    def __init__(self) -> None:
        self._events: Queue[
            _SubmitRequest
            | _IncomingFrame
            | _AwaitUnsolicited
            | _OpenBodeSubscription
            | _CloseBodeSubscription
            | _Transmitted
            | _TransmitFailed
            | _Stop
        ] = Queue()

        self._outgoing: Queue[OutgoingCommand | None] = Queue()
        self._completions: Queue[CompletionJob | None] = Queue()

        # Create trhead for dispather
        self._thread = Thread(
            target=self._run,
            name="sbgc-dispatcher",
            daemon=True,
        )

        self._started = Event()
        self._stopped = Event()
        self._state_lock = Lock()
        self._accepting_requests = False
        self._stop_future: Future[None] | None = None

        # This objects change by Dispatcher thread.
        self._request_generations = count(1)
        self._arrival_generations = count(1)
        self._pending_by_generation: dict[int, _PendingRequest] = {}
        self._pending_by_key: dict[ResponseKey, deque[_PendingRequest]] = defaultdict(deque)
        self._waiting_by_key: dict[ResponseKey, deque[_PendingRequest]] = defaultdict(deque)
        self._active_by_key: dict[ResponseKey, _PendingRequest] = {}
        self._deadlines: list[tuple[float, int]] = []
        self._unsolicited: Queue[ReceivedFrame] = Queue()
        self._unsolicited_waiter_generations = count(1)
        self._unsolicited_waiters: dict[int, deque[_UnsolicitedWaiter]] = defaultdict(deque)
        self._unsolicited_waiters_by_generation: dict[int, _UnsolicitedWaiter] = {}
        self._unsolicited_deadlines: list[tuple[float, int]] = []
        self._bode_subscription_generations = count(1)
        self._bode_subscription: BodeSubscription | None = None

        self._key_extractors: dict[int, KeyExtractor] = {}

    def start(self) -> None:
        with self._state_lock:
            if self._started.is_set():
                raise RuntimeError("Dispatcher is already started")

            self._accepting_requests = True
            self._started.set()
            self._thread.start()

    def request(
        self,
        command_id: int,
        payload: bytes = b"",
        *,
        response_command_id: int | None = None,
        response_key: ResponseKey | None = None,
        timeout: float | None = 1.0,
        route: str = "general",
        decoder: Decoder | None = None,
        complete_on_transmit: bool = False,
    ) -> Future[Any]:
        """Non blocking public entry."""

        if not 1 <= command_id <= 255:
            raise ValueError("command_id must be in range 1...255")

        if len(payload) > 255:
            raise ValueError("payload cannot exceed 255 bytes")

        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be positive or None")

        if type(complete_on_transmit) is not bool:
            raise TypeError("complete_on_transmit must be bool")

        if response_command_id is None:
            expected_id = command_id
        else:
            expected_id = response_command_id

        if response_key is None:
            key = ("command", expected_id)
        else:
            key = response_key

        future: Future[Any] = Future()

        with self._state_lock:
            if not self._started.is_set():
                raise RuntimeError("Call dispatcher.start() before request()")
            if not self._accepting_requests:
                raise ConnectionError("Dispatcher is stopped")

            self._events.put(
                _SubmitRequest(
                    command_id=command_id,
                    payload=bytes(payload),
                    response_command_id=expected_id,
                    response_key=key,
                    timeout=timeout,
                    route=route,
                    decoder=(lambda frame: frame) if decoder is None else decoder,
                    future=future,
                    complete_on_transmit=complete_on_transmit,
                )
            )

        return future

    def send(
        self,
        command_id: int,
        payload: bytes = b"",
        *,
        route: str = "general",
    ) -> Future[None]:
        """Queue a command and complete when TX successfully writes it.

        This is for SerialAPI commands which intentionally do not return a
        response. A serial-write failure still completes the Future with that
        exception.
        """

        return self.request(
            command_id,
            payload,
            route=route,
            decoder=lambda _frame: None,
            complete_on_transmit=True,
        )

    # for test
    def take_outgoing(self, timeout: float | None = None) -> OutgoingCommand | None:
        """Get the next command for the TX thread."""

        return self._outgoing.get(timeout=timeout)

    # for test
    @property
    def completion_queue(self) -> Queue[CompletionJob | None]:
        """Internal queue consumed by `WorkerManager`."""

        return self._completions

    def take_unsolicited(self, timeout: float | None = None) -> ReceivedFrame:
        """Get a frame not matched to an already transmitted request.

        This is the hand-off point for telemetry and future subscribers.
        """

        return self._unsolicited.get(timeout=timeout)

    def receive_unsolicited(
        self,
        command_id: int,
        *,
        timeout: float | None = 1.0,
        route: str = "general",
        decoder: Decoder | None = None,
    ) -> Future[Any]:
        """Return a Future for the next unmatched frame with ``command_id``.

        Stream data is intentionally handled separately from request replies:
        it can never consume a pending request, and decoding still happens in
        the selected worker route.
        """

        if not 1 <= command_id <= 255:
            raise ValueError("command_id must be in range 1...255")
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be positive or None")
        future: Future[Any] = Future()
        with self._state_lock:
            if not self._started.is_set():
                raise RuntimeError("Call dispatcher.start() before receive_unsolicited()")
            if not self._accepting_requests:
                raise ConnectionError("Dispatcher is stopped")
            self._events.put(
                _AwaitUnsolicited(
                    command_id=command_id,
                    timeout=timeout,
                    route=route,
                    decoder=(lambda frame: frame) if decoder is None else decoder,
                    future=future,
                )
            )
        return future

    def open_bode_subscription(self, *, timeout: float | None = 1.0) -> BodeSubscription:
        """Reserve exclusive delivery of the next Bode-test stream.

        Call this before transmitting ``CMD_BODE_TEST_START_STOP``.  The
        controller protocol exposes no test identifier in CMD #38 packets, so
        only one subscription may exist for a physical port at a time.
        """

        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be positive or None")

        future: Future[BodeSubscription] = Future()
        with self._state_lock:
            if not self._started.is_set():
                raise RuntimeError("Call dispatcher.start() before open_bode_subscription()")
            if not self._accepting_requests:
                raise ConnectionError("Dispatcher is stopped")
            self._events.put(_OpenBodeSubscription(future))

        return future.result(timeout=timeout)

    def close_bode_subscription(self, generation: int) -> None:
        """Release a Bode subscription if it is still the active one."""

        with self._state_lock:
            if self._accepting_requests:
                self._events.put(_CloseBodeSubscription(generation))

    # helpers
    def submit_incoming(self, frame: WireFrame) -> None:
        """Call only RX thread."""

        self._events.put(_IncomingFrame(frame))

    def submit_transmitted(self, generation: int) -> None:
        """Call TX thread after successful serial.write()."""

        self._events.put(_Transmitted(generation))

    def submit_transmit_failed(self, generation: int, error: BaseException) -> None:
        """Call TX thread, if serial.write() complited with error."""

        self._events.put(_TransmitFailed(generation, error))

    def take_completion(self) -> CompletionJob | None:

        return self._completions.get()

    def register_key_extractor(
        self,
        response_command_id: int,
        extractor: KeyExtractor,
    ) -> None:

        if self._started.is_set():
            raise RuntimeError("Register key extractors before dispatcher.start()")
        if not 1 <= response_command_id <= 255:
            raise ValueError("response_command_id must be in range 1...255")

        self._key_extractors[response_command_id] = extractor

    def stop(self) -> Future[None]:
        """Non blocking stop of dispatcher."""

        with self._state_lock:
            if self._stop_future is not None:
                return self._stop_future

            completed: Future[None] = Future()
            self._stop_future = completed
            self._accepting_requests = False

            if self._stopped.is_set() or not self._started.is_set():
                self._stopped.set()
                completed.set_result(None)
            else:
                self._events.put(_Stop(completed))

            return completed

    def join(self, timeout: float | None = None) -> None:
        """Wait until the dispatcher thread has finished."""

        self._thread.join(timeout)

    def _run(self) -> None:
        try:
            while True:
                self._expire_due_requests()

                try:
                    event = self._events.get(timeout=self._next_wait_timeout())
                except Empty:
                    continue

                if isinstance(event, _SubmitRequest):
                    self._handle_submit(event)

                elif isinstance(event, _IncomingFrame):
                    self._handle_incoming(event.frame)

                elif isinstance(event, _AwaitUnsolicited):
                    self._handle_await_unsolicited(event)

                elif isinstance(event, _OpenBodeSubscription):
                    self._handle_open_bode_subscription(event)

                elif isinstance(event, _CloseBodeSubscription):
                    self._handle_close_bode_subscription(event.generation)

                elif isinstance(event, _Transmitted):
                    self._handle_transmitted(event.generation)

                elif isinstance(event, _TransmitFailed):
                    self._handle_transmit_failed(event.generation, event.error)

                elif isinstance(event, _Stop):
                    self._handle_stop(event.completed)
                    return

        finally:
            with self._state_lock:
                self._accepting_requests = False
            self._stopped.set()

    def _handle_submit(self, event: _SubmitRequest) -> None:
        generation = next(self._request_generations)

        pending = _PendingRequest(
            generation=generation,
            command_id=event.command_id,
            payload=event.payload,
            response_key=event.response_key,
            timeout=event.timeout,
            route=event.route,
            decoder=event.decoder,
            future=event.future,
            complete_on_transmit=event.complete_on_transmit,
        )

        self._pending_by_generation[generation] = pending
        self._waiting_by_key[event.response_key].append(pending)
        self._dispatch_next_for_key(event.response_key)

    def _dispatch_next_for_key(self, key: ResponseKey) -> None:
        """Allow one request per response key onto the physical port."""

        if key in self._active_by_key:
            return

        waiting = self._waiting_by_key.get(key)
        if not waiting:
            return

        pending = waiting.popleft()
        if not waiting:
            del self._waiting_by_key[key]

        pending.dispatched = True
        self._active_by_key[key] = pending
        self._outgoing.put(
            OutgoingCommand(
                generation=pending.generation,
                command_id=pending.command_id,
                payload=pending.payload,
            )
        )

    def _handle_transmitted(self, generation: int) -> None:
        pending = self._pending_by_generation.get(generation)

        if pending is None or pending.transmitted:
            return

        pending.transmitted = True
        if pending.complete_on_transmit:
            completed = self._remove_pending(generation)
            if completed is None:
                return
            self._completions.put(
                CompletionJob(
                    route=completed.route,
                    future=completed.future,
                    received=ReceivedFrame(
                        arrival_generation=next(self._arrival_generations),
                        request_generation=completed.generation,
                        response_key=completed.response_key,
                        wire=WireFrame(0, completed.command_id, b""),
                    ),
                    decoder=completed.decoder,
                    error=None,
                )
            )
            return
        self._pending_by_key[pending.response_key].append(pending)

        if pending.timeout is None:
            return
        pending.deadline = monotonic() + pending.timeout
        heappush(self._deadlines, (pending.deadline, generation))

    def _handle_await_unsolicited(self, event: _AwaitUnsolicited) -> None:
        waiter = _UnsolicitedWaiter(
            generation=next(self._unsolicited_waiter_generations),
            command_id=event.command_id,
            timeout=event.timeout,
            route=event.route,
            decoder=event.decoder,
            future=event.future,
        )
        self._unsolicited_waiters[event.command_id].append(waiter)
        self._unsolicited_waiters_by_generation[waiter.generation] = waiter
        if event.timeout is not None:
            waiter.deadline = monotonic() + event.timeout
            heappush(self._unsolicited_deadlines, (waiter.deadline, waiter.generation))

    def _handle_open_bode_subscription(self, event: _OpenBodeSubscription) -> None:
        if self._bode_subscription is not None:
            event.future.set_exception(RuntimeError("A Bode test is already active"))
            return

        subscription = BodeSubscription(self, next(self._bode_subscription_generations))
        self._bode_subscription = subscription
        event.future.set_result(subscription)

    def _handle_close_bode_subscription(self, generation: int) -> None:
        subscription = self._bode_subscription
        if subscription is None or subscription.generation != generation:
            return

        self._bode_subscription = None
        subscription._close_locally()

    def _handle_transmit_failed(self, generation: int, error: BaseException) -> None:
        pending = self._remove_pending(generation)

        if pending is None:
            return

        self._completions.put(
            CompletionJob(
                route=pending.route,
                future=pending.future,
                received=None,
                decoder=None,
                error=error,
            )
        )

    def _handle_incoming(self, frame: WireFrame) -> None:
        key = self._key_for_frame(frame)
        pending = self._pop_pending_for_key(key) if key is not None else None

        received = ReceivedFrame(
            arrival_generation=next(self._arrival_generations),
            request_generation=None if pending is None else pending.generation,
            response_key=key,
            wire=frame,
        )

        if pending is None:
            # This includes telemetry, stale replies and frames that arrive
            # before their request has been transmitted.
            subscription = self._bode_subscription
            if (
                subscription is not None
                and frame.command_id in (38, 37)
            ):
                subscription._submit(received)
                return

            waiter = self._pop_unsolicited_waiter(frame.command_id)
            if waiter is None:
                self._unsolicited.put(received)
            else:
                self._completions.put(
                    CompletionJob(waiter.route, waiter.future, received, waiter.decoder, None)
                )
            return

        self._completions.put(
            CompletionJob(
                route=pending.route,
                future=pending.future,
                received=received,
                decoder=pending.decoder,
                error=None,
            )
        )

    def _handle_stop(self, completed: Future[None]) -> None:
        for pending in tuple(self._pending_by_generation.values()):
            self._completions.put(
                CompletionJob(
                    route=pending.route,
                    future=pending.future,
                    received=None,
                    decoder=None,
                    error=ConnectionError("Serial dispatcher is stopped"),
                )
            )

        self._pending_by_generation.clear()
        self._pending_by_key.clear()
        self._waiting_by_key.clear()
        self._active_by_key.clear()
        self._deadlines.clear()
        for waiter in tuple(self._unsolicited_waiters_by_generation.values()):
            self._completions.put(
                CompletionJob(
                    route=waiter.route,
                    future=waiter.future,
                    received=None,
                    decoder=None,
                    error=ConnectionError("Serial dispatcher is stopped"),
                )
            )
        self._unsolicited_waiters.clear()
        self._unsolicited_waiters_by_generation.clear()
        self._unsolicited_deadlines.clear()
        if self._bode_subscription is not None:
            self._bode_subscription._close_locally()
            self._bode_subscription = None

        # Wake TX and worker layers without polling.
        self._outgoing.put(None)
        self._completions.put(None)

        completed.set_result(None)

    def _key_for_frame(self, frame: WireFrame) -> ResponseKey | None:
        if frame.command_id in (self.CMD_CONFIRM, self.CMD_ERROR):
            if not frame.payload:
                return None
            return ("command", frame.payload[0])

        extractor = self._key_extractors.get(frame.command_id)

        if extractor is not None:
            return extractor(frame)

        return ("command", frame.command_id)

    def _pop_pending_for_key(self, key: ResponseKey) -> _PendingRequest | None:
        lane = self._pending_by_key.get(key)

        if not lane:
            return None

        pending = lane[0]
        return self._remove_pending(pending.generation)

    def _remove_pending(self, generation: int) -> _PendingRequest | None:
        pending = self._pending_by_generation.pop(generation, None)

        if pending is None:
            return None

        lane = self._pending_by_key.get(pending.response_key)
        if lane is not None:
            lane.remove(pending)
            if not lane:
                del self._pending_by_key[pending.response_key]
        else:
            waiting = self._waiting_by_key.get(pending.response_key)
            if waiting is not None:
                waiting.remove(pending)
                if not waiting:
                    del self._waiting_by_key[pending.response_key]

        if self._active_by_key.get(pending.response_key) is pending:
            del self._active_by_key[pending.response_key]
            self._dispatch_next_for_key(pending.response_key)

        return pending

    def _pop_unsolicited_waiter(self, command_id: int) -> _UnsolicitedWaiter | None:
        waiters = self._unsolicited_waiters.get(command_id)
        if not waiters:
            return None
        waiter = waiters.popleft()
        if not waiters:
            del self._unsolicited_waiters[command_id]
        self._unsolicited_waiters_by_generation.pop(waiter.generation, None)
        return waiter

    def _expire_due_requests(self) -> None:
        now = monotonic()

        while self._deadlines and self._deadlines[0][0] <= now:
            deadline, generation = heappop(self._deadlines)
            pending = self._pending_by_generation.get(generation)

            if pending is None or pending.deadline != deadline:
                continue

            self._remove_pending(generation)

            self._completions.put(
                CompletionJob(
                    route=pending.route,
                    future=pending.future,
                    received=None,
                    decoder=None,
                    error=CommandTimeoutError(f"Request generation={generation} timed out"),
                )
            )

        while self._unsolicited_deadlines and self._unsolicited_deadlines[0][0] <= now:
            deadline, generation = heappop(self._unsolicited_deadlines)
            waiter = self._unsolicited_waiters_by_generation.get(generation)
            if waiter is None or waiter.deadline != deadline:
                continue
            self._unsolicited_waiters_by_generation.pop(generation)
            queue = self._unsolicited_waiters[waiter.command_id]
            queue.remove(waiter)
            if not queue:
                del self._unsolicited_waiters[waiter.command_id]
            self._completions.put(
                CompletionJob(
                    waiter.route,
                    waiter.future,
                    None,
                    None,
                    CommandTimeoutError(f"Unsolicited command {waiter.command_id} timed out"),
                )
            )

    def _next_wait_timeout(self) -> float | None:
        while self._deadlines:
            deadline, generation = self._deadlines[0]
            pending = self._pending_by_generation.get(generation)

            if pending is None or pending.deadline != deadline:
                heappop(self._deadlines)
                continue
            break

        while self._unsolicited_deadlines:
            deadline, generation = self._unsolicited_deadlines[0]
            waiter = self._unsolicited_waiters_by_generation.get(generation)
            if waiter is None or waiter.deadline != deadline:
                heappop(self._unsolicited_deadlines)
                continue
            break

        deadlines: list[float] = []
        if self._deadlines:
            deadlines.append(self._deadlines[0][0])
        if self._unsolicited_deadlines:
            deadlines.append(self._unsolicited_deadlines[0][0])
        return None if not deadlines else max(0.0, min(deadlines) - monotonic())
