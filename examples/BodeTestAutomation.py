from __future__ import annotations

import argparse
from itertools import product
from math import isfinite
from pathlib import Path

from sbgc32 import BodeTestAxis, SimpleBGC
from sbgc32.modules.bode import (
    DEFAULT_POSITION_SETTLE_SECONDS,
    MINIMUM_TEST_DURATION_SECONDS,
    AxisTestSettings,
    Position,
    create_bode_plotter,
    csv_path_for_test,
    run_bode_test_at_position,
)

# User configuration ---------------------------------------------------------

TEST_DURATION_SECONDS = MINIMUM_TEST_DURATION_SECONDS
POSITION_SETTLE_SECONDS = DEFAULT_POSITION_SETTLE_SECONDS
SERIAL_PORT: str | None = None
DEFAULT_OUTPUT_DIR: Path | None = None
PLOT_ENABLED = False
PLOT_MODE = "axis"
OVERWRITE_EXISTING: bool | None = None


POSITIONS = tuple(
    Position(roll, pitch)
    for roll, pitch in product(
        (-30.0, 0.0, 30.0),
        (-90.0, -60.0, -30.0, 0.0, 30.0, 60.0, 90.0),
    )
)


AXIS_TESTS = {
    BodeTestAxis.ROLL: AxisTestSettings(True, 3000, 3, 200),
    BodeTestAxis.PITCH: AxisTestSettings(False, 3000, 3, 200),
    BodeTestAxis.YAW: AxisTestSettings(False, 3000, 3, 200),
}


LEAVE_MOTORS_ON = False
WAIT_FOR_AUTO_TASK_CONFIRMATION = True
SKIP_START_CONFIRMATION = False


class _ArgumentParser(argparse.ArgumentParser):
    """Show the full command reference when an argument is invalid."""

    def error(self, message: str) -> None:
        self.print_help()
        self.exit(2, f"\n{self.prog}: error: {message}\n")


def parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line options without requesting runtime parameters."""

    parser = _ArgumentParser(
        description="Run Bode tests for configured positions and save CSV files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--port",
        default=argparse.SUPPRESS,
        help="serial port, for example COM4 (optional; default: prompt)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=argparse.SUPPRESS,
        help="directory for CSV files (optional; default: file-selection dialog)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=TEST_DURATION_SECONDS,
        metavar="SECONDS",
        help="duration of one test in seconds (optional; default: %(default)g)",
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=POSITION_SETTLE_SECONDS,
        metavar="SECONDS",
        help="delay after reaching a position (optional; default: %(default)g)",
    )
    parser.add_argument(
        "--axes",
        choices=("roll", "pitch", "yaw"),
        nargs="+",
        metavar="AXIS",
        default=argparse.SUPPRESS,
        help="run only these enabled axes (optional; default: every enabled axis)",
    )
    parser.add_argument(
        "--overwrite",
        action=argparse.BooleanOptionalAction,
        default=argparse.SUPPRESS,
        help="replace existing CSV files (optional; default: prompt if files exist)",
    )
    parser.add_argument(
        "--plot",
        action=argparse.BooleanOptionalAction,
        default=PLOT_ENABLED,
        help="show Bode plots; requires NumPy and Matplotlib (optional; default: %(default)s)",
    )
    parser.add_argument(
        "--plot-mode",
        choices=("axis", "file", "both"),
        default=PLOT_MODE,
        help="axis: one window per axis; file: one window per CSV; both: all windows "
        "(optional; default: %(default)s)",
    )
    parser.add_argument(
        "--leave-motors-on",
        action=argparse.BooleanOptionalAction,
        default=LEAVE_MOTORS_ON,
        help="leave motors on after a normal run (optional; default: %(default)s)",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        default=SKIP_START_CONFIRMATION,
        help="skip the motor safety confirmation (optional; default: %(default)s)",
    )

    parsed = parser.parse_args(arguments)
    if not isfinite(parsed.duration) or parsed.duration < MINIMUM_TEST_DURATION_SECONDS:
        parser.error(f"--duration must be at least {MINIMUM_TEST_DURATION_SECONDS:g} seconds")
    if not isfinite(parsed.settle_seconds) or parsed.settle_seconds < 0:
        parser.error("--settle-seconds must not be negative")

    return parsed


def _read_port(value: str | None) -> str:
    """Return a supplied COM port or request one for an IDE launch."""

    port = value or input("COM port number: ").strip()
    if not port:
        raise SystemExit("COM port was not specified.")

    return port if port.upper().startswith("COM") else f"COM{port}"


def _select_output_dir(value: Path | None) -> Path:
    """Return an explicit directory or show the native folder-selection dialog."""

    if value is not None:
        return value.expanduser()

    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        selected = ""

    else:
        try:
            root = tk.Tk()
        except tk.TclError:
            selected = ""
        else:
            root.withdraw()
            root.attributes("-topmost", True)
            try:
                selected = filedialog.askdirectory(title="Choose a directory for Bode CSV files")
            finally:
                root.destroy()

    if not selected:
        selected = input("Directory for Bode CSV files: ").strip()

    if not selected:
        raise SystemExit("Output directory selection was cancelled.")

    return Path(selected)


def _check_output_paths(
    output_dir: Path,
    axes: tuple[BodeTestAxis, ...],
    *,
    overwrite: bool | None,
) -> bool:
    """Stop before motion when the planned CSV names are unsafe to use."""

    planned_paths = tuple(
        csv_path_for_test(output_dir, axis, position) for position in POSITIONS for axis in axes
    )

    duplicate_paths = {path for path in planned_paths if planned_paths.count(path) > 1}

    if duplicate_paths:
        names = "\n".join(f"  {path.name}" for path in sorted(duplicate_paths))
        raise ValueError(f"The test plan contains duplicate CSV names:\n{names}")

    existing_paths = tuple(path for path in planned_paths if path.exists())
    if not existing_paths:
        return bool(overwrite)

    names = "\n".join(f"  {path.name}" for path in existing_paths)

    if overwrite is None:
        answer = (
            input(f"CSV files already exist:\n{names}\nOverwrite them? [y/n]: ").strip().casefold()
        )
        if answer not in {"y", "yes"}:
            raise SystemExit("Existing CSV files were left unchanged. Program stopped.")
    elif not overwrite:
        raise FileExistsError(
            f"CSV files already exist:\n{names}\nUse --overwrite to replace them."
        )

    print(f"The following CSV files will be replaced:\n{names}")
    return True


# Main function ---------------------------------------------------------


def main() -> None:
    args = parse_args()

    port = _read_port(getattr(args, "port", SERIAL_PORT))
    output_dir = _select_output_dir(getattr(args, "output_dir", DEFAULT_OUTPUT_DIR))
    output_dir.mkdir(parents=True, exist_ok=True)

    enabled_axes = tuple(axis for axis, settings in AXIS_TESTS.items() if settings.enabled)

    if not enabled_axes:
        raise ValueError("Enable at least one axis in AXIS_TESTS")

    requested_axis_names = getattr(args, "axes", None)
    if requested_axis_names is not None:
        requested_axes = tuple(BodeTestAxis[axis.upper()] for axis in requested_axis_names)
        disabled_axes = tuple(axis for axis in requested_axes if axis not in enabled_axes)
        if disabled_axes:
            names = ", ".join(axis.name for axis in disabled_axes)
            raise ValueError(f"Requested axis is disabled in AXIS_TESTS: {names}")
        enabled_axes = requested_axes

    overwrite = _check_output_paths(
        output_dir,
        enabled_axes,
        overwrite=getattr(args, "overwrite", OVERWRITE_EXISTING),
    )

    plotter = create_bode_plotter(args.plot, mode=args.plot_mode)
    total_tests = len(POSITIONS) * len(enabled_axes)

    print(f"Count of tests: {total_tests}")
    print(f"Tests will safe in {output_dir.resolve()}")
    print("---------------------------------------------------------")

    print("WARNING! The gimbal will move through all specified positions.")

    if not args.yes:
        input("Ensure the work area is clear and press Enter to start. ")

    with SimpleBGC(port=port) as gimbal:
        motors_may_be_on = False
        interrupted = False

        try:
            # Set this before the request, so Ctrl+C during motors_on is also safe.
            motors_may_be_on = True
            gimbal.motors_on().result()

            completed_tests = 0

            for position in POSITIONS:
                for axis in enabled_axes:
                    completed_tests += 1

                    print(
                        f"[{completed_tests}/{total_tests}] {axis.name}: "
                        f"R={position.roll:g}, P={position.pitch:g}, Y={position.yaw:g}",
                        flush=True,
                    )

                    record = run_bode_test_at_position(
                        gimbal,
                        axis,
                        AXIS_TESTS[axis],
                        position,
                        output_dir=output_dir,
                        test_duration_seconds=args.duration,
                        overwrite=overwrite,
                        position_settle_seconds=args.settle_seconds,
                        wait_for_position_confirmation=WAIT_FOR_AUTO_TASK_CONFIRMATION,
                    )

                    result = record.result

                    status = "Ok" if result.successful else "Incomplete / With error"

                    if result.confirmation is None:
                        print(
                            "Warning: CMD_CONFIRM was not received. "
                            "The test was accepted after receiving Bode data.",
                            flush=True,
                        )

                    if result.completion_reports_last_sample_index:
                        samples_text = f"samples {result.received_samples_count} "
                    else:
                        samples_text = (
                            f"samples {result.received_samples_count} / "
                            f"{result.completion.samples_count}"
                        )

                    print(
                        f"  {status}: {samples_text}, error={result.completion.error_code}; "
                        f"{record.csv_path}",
                        flush=True,
                    )

                    if not result.samples_match and result.data_packet_counters:
                        counters = result.data_packet_counters
                        packet_sizes = result.data_packet_sample_counts
                        print(
                            "  Bode diagnostics: "
                            f"packets={len(counters)}, samples/packet="
                            f"{min(packet_sizes)}..{max(packet_sizes)}, "
                            f"counter={counters[0]}..{counters[-1]}, "
                            f"counter jumps={result.sample_counter_discontinuities}",
                            flush=True,
                        )

                    if plotter is not None:
                        plotter.add(record)

        except KeyboardInterrupt:
            interrupted = True
            print("Interrupted. Switching motors off.", flush=True)
            raise

        finally:
            if motors_may_be_on and (interrupted or not args.leave_motors_on):
                gimbal.motors_off().result()
                print("Motors off.", flush=True)

    if plotter is not None:
        plotter.show()


if __name__ == "__main__":
    main()
