from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path

from sbgc32 import BodeTestAxis, SimpleBGC
from sbgc32.modules.bode import (
    DEFAULT_POSITION_SETTLE_SECONDS,
    DEFAULT_RECOVERY_SECONDS,
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
RECOVERY_SECONDS = DEFAULT_RECOVERY_SECONDS
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


# Helpers ---------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", help="Serial port, for example COM4")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="directory for CSV files; otherwise a folder-selection dialog is shown",
    )
    parser.add_argument("--overwrite", action="store_true", help="replace existing CSV files")
    parser.add_argument(
        "--plot",
        action="store_true",
        help="show Bode plots without asking (requires NumPy and Matplotlib)",
    )
    parser.add_argument(
        "--plot-mode",
        choices=("axis", "file", "both"),
        help="axis: one window per axis; file: one window per CSV; both: all windows",
    )
    parser.add_argument("--leave-motors-on", action="store_true")
    parser.add_argument("--yes", action="store_true", help="skip the motor safety confirmation")

    return parser.parse_args()


def _read_port(value: str | None) -> str:
    if value:
        return value
    port = input("COM port number: ").strip()

    return port if port.upper().startswith("COM") else f"COM{port}"


def _read_output_dir(value: Path | None) -> Path:
    """Return an explicit output directory or ask the user to select one."""

    if value is not None:
        return value.expanduser()

    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        tk = None

    else:
        try:
            root = tk.Tk()
        except tk.TclError:
            root = None

        if root is not None:
            root.withdraw()
            root.attributes("-topmost", True)

            try:
                selected = filedialog.askdirectory(title="Chose catalog for Bode CSV")
            finally:
                root.destroy()

            if not selected:
                raise SystemExit("Catalog selection cancelled.")

            return Path(selected)

    print("The folder selection window is unavailable. Please, specify the path in the console.")

    selected = input("Catalog for CSV files: ").strip()
    if not selected:
        raise SystemExit("Catalog for CSV do not select.")

    return Path(selected).expanduser()


def _read_plot_requested(force_enabled: bool) -> bool:
    """Ask for optional plotting unless it was explicitly enabled by a flag."""
    if force_enabled:
        return True
    answer = input("Use visualization [y/n]: ").strip().casefold()
    return answer in {"y", "yes"}


def _read_plot_mode(enabled: bool, specified_mode: str | None, *, force_enabled: bool) -> str:
    """Choose where optional Bode plots appear."""
    if specified_mode is not None:
        return specified_mode
    if not enabled or force_enabled:
        return "axis"

    answer = input("Plot mode: [f]ile, [w]indows, or [b]oth: ").strip().casefold()
    return {"f": "file", "file": "file", "b": "both", "both": "both"}.get(answer, "axis")


def _check_output_paths(
    output_dir: Path,
    axes: tuple[BodeTestAxis, ...],
    *,
    overwrite: bool,
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
        return overwrite

    names = "\n".join(f"  {path.name}" for path in existing_paths)

    if not overwrite:
        answer = (
            input(f"CSV files already exist:\n{names}\nOverwrite them? [y/n]: ").strip().casefold()
        )
        if answer not in {"y", "yes"}:
            raise SystemExit("Existing CSV files were left unchanged. Program stopped.")
        overwrite = True

    print(f"The following CSV files will be replaced:\n{names}")
    return overwrite


# Main function ---------------------------------------------------------


def main() -> None:
    args = parse_args()

    port = _read_port(args.port)

    output_dir = _read_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    enabled_axes = tuple(axis for axis, settings in AXIS_TESTS.items() if settings.enabled)

    if not enabled_axes:
        raise ValueError("Enable at least one axis in AXIS_TESTS")

    overwrite = _check_output_paths(output_dir, enabled_axes, overwrite=args.overwrite)

    plot_requested = _read_plot_requested(args.plot)
    plot_mode = _read_plot_mode(plot_requested, args.plot_mode, force_enabled=args.plot)
    plotter = create_bode_plotter(plot_requested, mode=plot_mode)
    total_tests = len(POSITIONS) * len(enabled_axes)

    print(f"Count of tests: {total_tests}")
    print(f"Tests will safe in {output_dir.resolve()}")
    print("---------------------------------------------------------")

    print("WARNING! The gimbal will move through all specified positions.")

    if not args.yes:
        input("Ensure the work area is clear and press Enter to start. ")

    with SimpleBGC(port=port) as gimbal:
        gimbal.motors_on().result()

        try:
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
                        test_duration_seconds=TEST_DURATION_SECONDS,
                        overwrite=overwrite,
                        position_settle_seconds=POSITION_SETTLE_SECONDS,
                        recovery_seconds=RECOVERY_SECONDS,
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
                        samples_text = (
                            f"samples {result.received_samples_count} "
                            f"(last index {result.completion.samples_count})"
                        )
                    else:
                        samples_text = (
                            f"samples {result.received_samples_count}/"
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

        finally:
            if not args.leave_motors_on:
                gimbal.motors_off().result()
                print("Motors off.", flush=True)

    if plotter is not None:
        plotter.show()


if __name__ == "__main__":
    main()
