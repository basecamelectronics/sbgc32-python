from __future__ import annotations

from concurrent.futures import InvalidStateError
from dataclasses import dataclass
from queue import Queue
from threading import Event, Thread
from typing import Any

from .dispatcher import CompletionJob


@dataclass(frozen=True, slots=True)
class WorkerRoute:
    """Settings of one class of worker."""

    name: str
    workers: int = 1  # One worker for class.
    queue_size: int = 100


DEFAULT_WORKER_ROUTES = (
    WorkerRoute("realtime", workers=1, queue_size=200),
    WorkerRoute("service", workers=1, queue_size=200),
    WorkerRoute("adjvars", workers=2, queue_size=100),
    WorkerRoute("calib", workers=1, queue_size=200),
    WorkerRoute("control", workers=2, queue_size=10),
    WorkerRoute("imu", workers=1, queue_size=200),
    WorkerRoute("profiles", workers=1, queue_size=200),
    WorkerRoute("eeprom", workers=1, queue_size=50),
    WorkerRoute("general", workers=8, queue_size=100),
)


class WorkerManager:
    def __init__(
        self,
        completion_queue: Queue[CompletionJob | None],
        routes: tuple[WorkerRoute, ...],
    ) -> None:
        self._completion_queue = completion_queue
        self._routes = {route.name: route for route in routes}
        self._inboxes: dict[str, Queue[CompletionJob | None]] = {}
        self._queues: dict[str, Queue[CompletionJob | None]] = {}
        self._threads: list[Thread] = []
        self._route_threads: list[Thread] = []
        self._started = Event()
        self._stopped = Event()
        self._stop_requested = Event()

        for route in routes:
            if route.name in self._queues:
                raise ValueError(f"Duplicate worker route: {route.name}")
            if route.workers < 1:
                raise ValueError("Each worker route must have at least one worker")
            if route.queue_size < 1:
                raise ValueError("Each worker route must have a positive queue size")

            inbox: Queue[CompletionJob | None] = Queue()
            queue: Queue[CompletionJob | None] = Queue(
                maxsize=route.queue_size,
            )
            self._inboxes[route.name] = inbox
            self._queues[route.name] = queue

            self._route_threads.append(
                Thread(
                    target=self._route_loop,
                    args=(route, inbox, queue),
                    name=f"sbgc-worker-route-{route.name}",
                    daemon=True,
                )
            )

            for index in range(route.workers):
                thread = Thread(
                    target=self._worker_loop,
                    args=(route.name, queue),
                    name=f"sbgc-worker-{route.name}-{index}",
                    daemon=True,
                )
                self._threads.append(thread)

        if "general" not in self._queues:
            raise ValueError("A 'general' worker route is required")

        self._router_thread = Thread(
            target=self._router_loop,
            name="sbgc-worker-router",
            daemon=True,
        )

    def start(self) -> None:
        """Start worker threads and the CompletionJob router."""

        if self._started.is_set():
            raise RuntimeError("WorkerManager is already started")

        self._started.set()

        for thread in self._threads:
            thread.start()

        for thread in self._route_threads:
            thread.start()

        self._router_thread.start()

    def stop(self) -> None:
        """Stop workers when the dispatcher is not managing their shutdown."""

        if not self._stop_requested.is_set():
            self._stop_requested.set()
            self._completion_queue.put(None)

    def join(self, timeout: float | None = None) -> None:
        self._router_thread.join(timeout)

        for thread in self._route_threads:
            thread.join(timeout)

        for thread in self._threads:
            thread.join(timeout)

    def _router_loop(self) -> None:
        """Receives job from dispatcher and put into the route queue."""

        try:
            while True:
                job = self._completion_queue.get()

                if job is None:
                    break

                inbox = self._inboxes.get(job.route, self._inboxes["general"])
                inbox.put(job)
        finally:
            self._stopped.set()

            for inbox in self._inboxes.values():
                inbox.put(None)

    @staticmethod
    def _route_loop(
        route: WorkerRoute,
        inbox: Queue[CompletionJob | None],
        queue: Queue[CompletionJob | None],
    ) -> None:
        """Transfer one route without blocking the shared completion router."""

        while True:
            job = inbox.get()

            if job is None:
                for _ in range(route.workers):
                    queue.put(None)
                return

            queue.put(job)

    def _worker_loop(
        self,
        route_name: str,
        queue: Queue[CompletionJob | None],
    ) -> None:
        """Decode and complete requests on the selected worker thread."""

        while True:
            job = queue.get()

            if job is None:
                return

            if job.future.done():
                # The caller might have cancelled it before the worker started.
                continue

            if job.error is not None:
                self._complete_error(job, job.error)
                continue

            if job.received is None or job.decoder is None:
                self._complete_error(
                    job,
                    RuntimeError(f"Worker route {route_name!r} received an invalid job"),
                )
                continue

            try:
                result = job.decoder(job.received.wire)
            except BaseException as error:
                self._complete_error(job, error)
            else:
                self._complete_result(job, result)

    @staticmethod
    def _complete_result(job: CompletionJob, result: Any) -> None:
        try:
            job.future.set_result(result)
        except InvalidStateError:
            # Future was cancelled while this worker decoded the payload.
            pass

    @staticmethod
    def _complete_error(job: CompletionJob, error: BaseException) -> None:
        try:
            job.future.set_exception(error)
        except InvalidStateError:
            # Future was cancelled while this worker handled the error.
            pass
