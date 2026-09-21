from __future__ import annotations

import csv
import struct
from concurrent.futures import Future
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from queue import Empty
from time import sleep
from typing import TYPE_CHECKING, Any

from ..commands import Command
from ..dispatcher import BodeSubscription
from ..protocol import WireFrame
from ..types import (
    BodeStimulusType,
    BodeTestAxis,
    BodeTestConfig,
    BodeTestData,
    BodeTestFinished,
    BodeTestResult,
    BodeTestSample,
    BodeTestSystem,
    CommandConfirmation,
    ConfirmationStatus,
    ControlAxis,
    ControlFlag,
    ControlMode,
)
from .realtime import decode_confirmation

if TYPE_CHECKING:
    from ..device import SimpleBGC


_BODE_DATA_HEADER_FORMAT = "<B4f"
_BODE_FINISHED_FORMAT = "<IHB15x"
BODE_SAMPLE_PERIOD_SECONDS = 0.0008
MINIMUM_TEST_DURATION_SECONDS = 4.0
DEFAULT_POSITION_SETTLE_SECONDS = 2.0
DEFAULT_RECOVERY_SECONDS = 1.0


@dataclass(frozen=True, slots=True)
class Position:
    """Euler pose used before a Bode test, in degrees."""

    roll: float
    pitch: float
    yaw: float = 0.0


@dataclass(frozen=True, slots=True)
class AxisTestSettings:
    """Per-axis settings for a white-noise Bode-test series."""

    enabled: bool
    stimulus_gain: int
    start_frequency_hz: int
    end_frequency_hz: int
    system: BodeTestSystem = BodeTestSystem.PLANT_OPEN_LOOP
    stimulus_type: BodeStimulusType = BodeStimulusType.WHITE_NOISE


@dataclass(frozen=True, slots=True)
class BodeTestRecord:
    """One saved Bode test and the pose at which it was acquired."""

    axis: BodeTestAxis
    position: Position
    csv_path: Path
    result: BodeTestResult


def _uint(value: object, name: str, maximum: int, *, minimum: int = 0) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer in range {minimum}..{maximum}")

    return value


def _samples_for_duration(duration_seconds: object) -> int:
    if (
        isinstance(duration_seconds, bool)
        or not isinstance(duration_seconds, (int, float))
        or not isfinite(duration_seconds)
        or duration_seconds < MINIMUM_TEST_DURATION_SECONDS
    ):
        raise ValueError(
            "test_duration_seconds must be a finite number of at least "
            f"{MINIMUM_TEST_DURATION_SECONDS:g} seconds"
        )

    return _uint(
        round(duration_seconds / BODE_SAMPLE_PERIOD_SECONDS),
        "test_duration_seconds converted to samples_num",
        0xFFFFFFFF,
        minimum=1,
    )


def encode_bode_test_start(config: BodeTestConfig) -> bytes:
    """Encode the 30-byte CMD_BODE_TEST_START_STOP start payload."""

    if not isinstance(config, BodeTestConfig):
        raise TypeError("config must be BodeTestConfig")

    try:
        axis = BodeTestAxis(config.axis)
        stimulus_type = BodeStimulusType(config.stimulus_type)
        system = BodeTestSystem(config.system)

    except ValueError as error:
        raise ValueError("config contains an unsupported Bode-test enum value") from error

    gain = _uint(config.stimulus_gain, "stimulus_gain", 65535, minimum=1)
    end_frequency = _uint(config.end_frequency_hz, "end_frequency_hz", 65535)
    samples_num = _samples_for_duration(config.test_duration_seconds)
    start_frequency = _uint(config.start_frequency_hz, "start_frequency_hz", 65535)
    mode = _uint(config.mode, "mode", 255)

    if mode != 0:
        raise ValueError("Bode-test mode is reserved and must be 0")

    if start_frequency > end_frequency:
        raise ValueError("start_frequency_hz cannot exceed end_frequency_hz")

    return struct.pack(
        "<BBHHBIBH16x",
        int(axis),
        int(stimulus_type),
        gain,
        end_frequency,
        int(system),
        samples_num,
        mode,
        start_frequency,
    )


def decode_bode_test_data(frame: WireFrame) -> BodeTestData:
    """Decode one unsolicited CMD_BODE_TEST_DATA packet."""

    if frame.command_id != int(Command.CMD_BODE_TEST_DATA):
        raise ValueError("expected CMD_BODE_TEST_DATA")

    payload = frame.payload
    header_size = struct.calcsize(_BODE_DATA_HEADER_FORMAT)

    if len(payload) < header_size or (len(payload) - header_size) % 4:
        raise ValueError("invalid CMD_BODE_TEST_DATA payload size")

    sample_counter, input_min, output_min, input_max, output_max = struct.unpack_from(
        _BODE_DATA_HEADER_FORMAT,
        payload,
    )

    raw_samples = tuple(struct.iter_unpack("<HH", payload[header_size:]))

    if len(raw_samples) > 20:
        raise ValueError("CMD_BODE_TEST_DATA contains more than 20 sample pairs")

    input_scale = (input_max - input_min) / 65534.0
    output_scale = (output_max - output_min) / 65534.0

    samples = tuple(
        BodeTestSample(
            input_value=input_raw * input_scale + input_min,
            output_value=output_raw * output_scale + output_min,
        )
        for input_raw, output_raw in raw_samples
    )

    return BodeTestData(
        sample_counter=sample_counter,
        input_min=input_min,
        output_min=output_min,
        input_max=input_max,
        output_max=output_max,
        samples=samples,
    )


def decode_bode_test_finished(frame: WireFrame) -> BodeTestFinished:
    """Decode the final unsolicited CMD_BODE_TEST_START_STOP packet."""

    if frame.command_id != int(Command.CMD_BODE_TEST_START_STOP):
        raise ValueError("expected final CMD_BODE_TEST_START_STOP")

    if len(frame.payload) != struct.calcsize(_BODE_FINISHED_FORMAT):
        raise ValueError("invalid final CMD_BODE_TEST_START_STOP payload size")

    samples_count, error_code, mode = struct.unpack(_BODE_FINISHED_FORMAT, frame.payload)

    return BodeTestFinished(
        samples_count=samples_count,
        error_code=error_code,
        mode=mode,
    )


class BodeTestStream:
    """Subscription to Bode data and the completion notification."""

    def __init__(self, subscription: BodeSubscription) -> None:
        self._subscription = subscription
        self._finished = False

    @property
    def finished(self) -> bool:
        return self._finished

    def get(self, timeout: float | None = None) -> BodeTestData | BodeTestFinished:
        frame = self._subscription.get(timeout=timeout).wire

        if frame.command_id == int(Command.CMD_BODE_TEST_DATA):
            return decode_bode_test_data(frame)

        if frame.command_id == int(Command.CMD_BODE_TEST_START_STOP):
            result = decode_bode_test_finished(frame)
            self._finished = True
            return result

        raise RuntimeError(f"unexpected Bode stream command {frame.command_id}")

    def close(self) -> None:
        self._subscription.close()


def open_bode_test_stream(self: SimpleBGC) -> BodeTestStream:
    """Prepare reception of CMD #38 and the final CMD #37 before starting a test."""

    return BodeTestStream(self._dispatcher.open_bode_subscription())


def start_bode_test(
    self: SimpleBGC,
    config: BodeTestConfig,
    *,
    timeout: float | None = 2.0,
) -> Future[CommandConfirmation]:
    """Start a Bode test and request its initial CMD_CONFIRM."""

    return self.request_raw(
        int(Command.CMD_BODE_TEST_START_STOP),
        encode_bode_test_start(config),
        response_command_id=int(Command.CMD_BODE_TEST_START_STOP),
        response_key=("command", int(Command.CMD_BODE_TEST_START_STOP)),
        timeout=timeout,
        route="calib",
        decoder=decode_confirmation,
    )


def run_bode_test(
    self: SimpleBGC,
    config: BodeTestConfig,
    *,
    start_timeout: float | None = 2.0,
    packet_timeout: float | None = 2.0,
) -> BodeTestResult:
    """Run one Bode test synchronously and return its complete data set.

    The Bode subscription is reserved before CMD #37 is transmitted, so the
    first CMD #38 packet cannot race the initial confirmation.  This blocks
    the caller only; the transport and dispatcher threads remain responsive.
    """

    stream = self.open_bode_test_stream()
    try:
        initial_packet: BodeTestData | BodeTestFinished | None = None
        try:
            confirmation = self.start_bode_test(config, timeout=start_timeout).result(start_timeout)
        except TimeoutError as confirmation_timeout:
            try:
                initial_packet = stream.get(timeout=packet_timeout)
            except Empty:
                raise confirmation_timeout

            confirmation = None

        if confirmation is not None and confirmation.status is not ConfirmationStatus.RECEIVED:
            raise RuntimeError(
                f"controller rejected Bode-test start (error code {confirmation.error_code})"
            )

        samples: list[BodeTestSample] = []
        data_packet_counters: list[int] = []
        data_packet_sample_counts: list[int] = []
        while True:
            if initial_packet is not None:
                packet = initial_packet
                initial_packet = None
            else:
                packet = stream.get(timeout=packet_timeout)
            if isinstance(packet, BodeTestData):
                samples.extend(packet.samples)
                data_packet_counters.append(packet.sample_counter)
                data_packet_sample_counts.append(len(packet.samples))
                continue

            return BodeTestResult(
                config=config,
                confirmation=confirmation,
                samples=tuple(samples),
                completion=packet,
                data_packet_counters=tuple(data_packet_counters),
                data_packet_sample_counts=tuple(data_packet_sample_counts),
            )
    finally:
        stream.close()


def _position_axes(position: Position) -> tuple[ControlAxis, ControlAxis, ControlAxis]:
    return (
        ControlAxis(
            mode=ControlMode.ANGLE | ControlFlag.AUTO_TASK,
            angle=position.roll,
        ),
        ControlAxis(
            mode=ControlMode.ANGLE | ControlFlag.AUTO_TASK,
            angle=position.pitch,
        ),
        ControlAxis(
            mode=ControlMode.ANGLE_REL_FRAME | ControlFlag.AUTO_TASK,
            angle=position.yaw,
        ),
    )


def move_to_position(
    self: SimpleBGC,
    position: Position,
    *,
    settle_seconds: float = DEFAULT_POSITION_SETTLE_SECONDS,
) -> None:
    """Move to an Euler pose and allow the automatically scheduled task to settle."""

    if not isfinite(settle_seconds) or settle_seconds < 0:
        raise ValueError("settle_seconds must be a finite non-negative number")

    self.control(_position_axes(position), need_confirmation=True).result()
    sleep(settle_seconds)


def make_bode_test_config(
    axis: BodeTestAxis,
    settings: AxisTestSettings,
    *,
    test_duration_seconds: float,
) -> BodeTestConfig:
    """Build one controller request from the duration and per-axis settings."""

    if not isinstance(settings, AxisTestSettings):
        raise TypeError("settings must be AxisTestSettings")

    return BodeTestConfig(
        axis=axis,
        stimulus_gain=settings.stimulus_gain,
        start_frequency_hz=settings.start_frequency_hz,
        end_frequency_hz=settings.end_frequency_hz,
        system=settings.system,
        stimulus_type=settings.stimulus_type,
        test_duration_seconds=test_duration_seconds,
    )


def csv_path_for_test(output_dir: Path, axis: BodeTestAxis, position: Position) -> Path:
    """Return the required AXIS_R*_P*_Y*.csv output filename."""

    def angle(value: float) -> str:
        return f"{value:g}"

    return output_dir / (
        f"{axis.name}_R{angle(position.roll)}_P{angle(position.pitch)}_Y{angle(position.yaw)}.csv"
    )


def save_bode_csv(path: Path, result: BodeTestResult, *, overwrite: bool) -> None:
    """Write samples in the CSV layout produced by the SimpleBGC GUI."""

    if path.exists() and not overwrite:
        raise FileExistsError(f"CSV already exists: {path}.")

    config = result.config
    with path.open("w", newline="", encoding="utf-8") as file:
        file.write(
            "%sbgc_test_data;"
            f"{int(config.system)};{int(config.axis)};{int(config.stimulus_type)};"
            f"{config.stimulus_gain};{config.start_frequency_hz};{config.end_frequency_hz}\n"
        )
        writer = csv.writer(file, delimiter=";", lineterminator="\n")
        writer.writerows((sample.input_value, sample.output_value) for sample in result.samples)


def run_bode_test_at_position(
    self: SimpleBGC,
    axis: BodeTestAxis,
    settings: AxisTestSettings,
    position: Position,
    *,
    output_dir: Path,
    test_duration_seconds: float,
    overwrite: bool,
    position_settle_seconds: float = DEFAULT_POSITION_SETTLE_SECONDS,
    recovery_seconds: float = DEFAULT_RECOVERY_SECONDS,
) -> BodeTestRecord:
    """Move, acquire, save, then return to neutral after one Bode test."""

    if not settings.enabled:
        raise ValueError(f"{axis.name} is disabled")
    if not isfinite(recovery_seconds) or recovery_seconds < 0:
        raise ValueError("recovery_seconds must be a finite non-negative number")

    neutral = Position(0.0, 0.0, 0.0)
    try:
        move_to_position(self, position, settle_seconds=position_settle_seconds)
        result = self.run_bode_test(
            make_bode_test_config(
                axis,
                settings,
                test_duration_seconds=test_duration_seconds,
            )
        )
        path = csv_path_for_test(output_dir, axis, position)
        save_bode_csv(path, result, overwrite=overwrite)
        return BodeTestRecord(axis=axis, position=position, csv_path=path, result=result)
    finally:
        move_to_position(self, neutral, settle_seconds=position_settle_seconds)
        sleep(recovery_seconds)


def _calculate_bode(result: BodeTestResult, numpy: Any) -> tuple[Any, Any, Any]:
    """Estimate output/input transfer response with overlapped Hann windows."""

    input_values = numpy.asarray([sample.input_value for sample in result.samples], dtype=float)
    output_values = numpy.asarray([sample.output_value for sample in result.samples], dtype=float)
    if len(input_values) < 64:
        raise ValueError("at least 64 Bode samples are required for a plot")

    segment_length = min(1024, 1 << (len(input_values).bit_length() - 1))
    window = numpy.hanning(segment_length)
    step = segment_length // 2
    spectrum_input = numpy.zeros(segment_length // 2 + 1, dtype=float)
    spectrum_cross = numpy.zeros(segment_length // 2 + 1, dtype=complex)
    segments = 0

    for start in range(0, len(input_values) - segment_length + 1, step):
        source = input_values[start : start + segment_length]
        response = output_values[start : start + segment_length]
        source_fft = numpy.fft.rfft((source - source.mean()) * window)
        response_fft = numpy.fft.rfft((response - response.mean()) * window)
        spectrum_input += numpy.abs(source_fft) ** 2
        spectrum_cross += numpy.conj(source_fft) * response_fft
        segments += 1

    spectrum_input /= segments
    spectrum_cross /= segments
    valid = spectrum_input > numpy.finfo(float).eps
    transfer = numpy.full(spectrum_cross.shape, numpy.nan + 0j)
    transfer[valid] = spectrum_cross[valid] / spectrum_input[valid]

    frequency = numpy.fft.rfftfreq(segment_length, d=BODE_SAMPLE_PERIOD_SECONDS)
    magnitude_db = 20.0 * numpy.log10(numpy.maximum(numpy.abs(transfer), numpy.finfo(float).tiny))
    phase_degrees = numpy.degrees(numpy.unwrap(numpy.angle(transfer)))
    mask = (
        valid
        & (frequency >= result.config.start_frequency_hz)
        & (frequency <= result.config.end_frequency_hz)
    )
    return frequency[mask], magnitude_db[mask], phase_degrees[mask]


@dataclass(slots=True)
class _BodePlotCurve:
    csv_name: str
    frequency: Any
    magnitude_db: Any
    phase_degrees: Any


@dataclass(slots=True)
class _BodePlotView:
    figure: Any
    magnitude_axis: Any
    phase_axis: Any
    vertical_line: Any
    magnitude_line: Any
    phase_line: Any
    annotation: Any
    curves: list[_BodePlotCurve]


class BodePlotter:
    """Interactive Bode views grouped by file, windows or both."""

    _MODES = frozenset(("file", "windows", "both"))

    def __init__(self, numpy: Any, pyplot: Any, *, mode: str = "file") -> None:
        if mode not in self._MODES:
            raise ValueError(f"plot mode must be one of {sorted(self._MODES)}")

        self._numpy = numpy
        self._pyplot = pyplot
        self._mode = mode
        self._axis_views: dict[BodeTestAxis, _BodePlotView] = {}
        self._views: list[_BodePlotView] = []
        self._record_count = 0
        self._pyplot.ion()

    def add(self, record: BodeTestRecord) -> None:
        """Add an acquired record to its selected interactive plot views."""

        frequency, magnitude_db, phase_degrees = _calculate_bode(record.result, self._numpy)
        if not len(frequency):
            print(f"{record.axis.name}: deficiency valid friquency for graphs.")

            return

        curve = _BodePlotCurve(record.csv_path.name, frequency, magnitude_db, phase_degrees)
        gain_color, phase_color, line_style = self._curve_style(self._record_count)
        self._record_count += 1

        if self._mode in {"file", "both"}:
            file_view = self._axis_views.get(record.axis)
            if file_view is None:
                file_view = self._create_view(f"Bode — {record.axis.name}")
                self._axis_views[record.axis] = file_view
            self._add_curve(file_view, curve, gain_color, phase_color, line_style)

        if self._mode in {"windows", "both"}:
            windows_view = self._create_view(f"Bode — {record.csv_path.name}")
            self._add_curve(windows_view, curve, gain_color, phase_color, line_style)

        self._pyplot.pause(0.001)

    def _create_view(self, title: str) -> _BodePlotView:
        figure, magnitude_axis = self._pyplot.subplots(num=title)
        phase_axis = magnitude_axis.twinx()
        figure.suptitle(title)
        magnitude_axis.set_xlabel("Frequency, Hz")
        magnitude_axis.set_ylabel("Amplitude, dB", color="tab:blue")
        phase_axis.set_ylabel("Phase, °", color="tab:red")
        magnitude_axis.grid(True, which="both")

        manager = getattr(figure.canvas, "manager", None)
        if manager is not None:
            manager.set_window_title(title)

        view = _BodePlotView(
            figure=figure,
            magnitude_axis=magnitude_axis,
            phase_axis=phase_axis,
            vertical_line=magnitude_axis.axvline(1, color="0.35", linestyle=":", visible=False),
            magnitude_line=magnitude_axis.axhline(
                0, color="tab:blue", linestyle=":", visible=False
            ),
            phase_line=phase_axis.axhline(0, color="tab:red", linestyle=":", visible=False),
            annotation=magnitude_axis.annotate(
                "",
                xy=(1, 0),
                xytext=(12, 12),
                textcoords="offset points",
                bbox={"boxstyle": "round", "fc": "white", "alpha": 0.85},
                visible=False,
            ),
            curves=[],
        )

        figure.canvas.mpl_connect(
            "motion_notify_event",
            lambda event, plot_view=view: self._update_cursor(event, plot_view),
        )

        self._views.append(view)
        return view

    def _add_curve(
        self,
        view: _BodePlotView,
        curve: _BodePlotCurve,
        gain_color: Any,
        phase_color: Any,
        line_style: str,
    ) -> None:

        view.curves.append(curve)
        view.magnitude_axis.semilogx(
            curve.frequency,
            curve.magnitude_db,
            color=gain_color,
            linestyle=line_style,
            label=f"gain {curve.csv_name}",
        )

        view.phase_axis.semilogx(
            curve.frequency,
            curve.phase_degrees,
            color=phase_color,
            linestyle=line_style,
            label=f"phase {curve.csv_name}",
        )

        view.magnitude_axis.legend(loc="upper left")
        view.phase_axis.legend(loc="upper right")
        view.figure.canvas.draw_idle()

    def _curve_style(self, index: int) -> tuple[Any, Any, str]:
        """Use distinct blue/red shades and line styles for each test record."""

        shade = 0.3 + 0.65 * ((index * 0.61803398875) % 1.0)
        line_style = ("-", "--", "-.", ":")[index // 8 % 4]

        return self._pyplot.cm.Blues(shade), self._pyplot.cm.Reds(shade), line_style

    def _update_cursor(self, event: Any, view: _BodePlotView) -> None:

        if event.inaxes not in (view.magnitude_axis, view.phase_axis) or event.xdata is None:
            self._hide_cursor(view)
            return

        if event.xdata <= 0 or not view.curves:
            self._hide_cursor(view)
            return

        use_phase = event.inaxes is view.phase_axis

        curve, sample_index = min(
            (self._nearest_curve_sample(event, use_phase, candidate) for candidate in view.curves),
            key=lambda candidate: candidate[0],
        )[1:]

        frequency = float(curve.frequency[sample_index])
        magnitude = float(curve.magnitude_db[sample_index])
        phase = float(curve.phase_degrees[sample_index])

        wrapped_phase = (phase + 180.0) % 360.0 - 180.0

        view.vertical_line.set_xdata((frequency, frequency))
        view.magnitude_line.set_ydata((magnitude, magnitude))
        view.phase_line.set_ydata((phase, phase))

        for artist in (view.vertical_line, view.magnitude_line, view.phase_line):
            artist.set_visible(True)

        view.annotation.xy = (frequency, magnitude)
        view.annotation.set_text(
            f"{curve.csv_name}\n{frequency:.3g} Hz\n"
            f"gain {magnitude:.2f} dB\n phase {wrapped_phase:.1f}°"
        )

        view.annotation.set_visible(True)
        view.figure.canvas.draw_idle()

    def _nearest_curve_sample(
        self, event: Any, use_phase: bool, curve: _BodePlotCurve
    ) -> tuple[float, _BodePlotCurve, int]:

        sample_index = int(
            self._numpy.argmin(
                self._numpy.abs(self._numpy.log(curve.frequency) - self._numpy.log(event.xdata))
            )
        )

        values = curve.phase_degrees if use_phase else curve.magnitude_db

        if event.ydata is None:
            distance = 0.0
        else:
            span = max(float(self._numpy.nanmax(values) - self._numpy.nanmin(values)), 1.0)
            distance = abs(float(values[sample_index]) - event.ydata) / span

        return distance, curve, sample_index

    @staticmethod
    def _hide_cursor(view: _BodePlotView) -> None:
        if not view.annotation.get_visible():
            return
        for artist in (view.vertical_line, view.magnitude_line, view.phase_line, view.annotation):
            artist.set_visible(False)
        view.figure.canvas.draw_idle()

    def show(self) -> None:
        if self._views:
            self._pyplot.ioff()
            self._pyplot.show()


def create_bode_plotter(enabled: bool, *, mode: str = "file") -> BodePlotter | None:
    """Create the optional plotter or print a clear dependency warning."""

    if not enabled:
        return None

    missing_packages: list[str] = []

    try:
        import numpy
    except ImportError:
        missing_packages.append("numpy")

    try:
        import matplotlib.pyplot as pyplot
    except ImportError:
        missing_packages.append("matplotlib")

    if missing_packages:
        print(
            "WARNING! do not downloaded libraries."
            f"{', '.join(missing_packages)}.Graphs do not showes; "
            "CSV will save. To download libraries, use commands: "
            "py -m pip install numpy matplotlib"
        )

        return None

    return BodePlotter(numpy, pyplot, mode=mode)
