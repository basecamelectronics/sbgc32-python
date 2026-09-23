Bode test automation
====================

``examples/BodeTestAutomation.py`` runs a Bode test over a grid of camera
positions and saves a CSV file for every completed axis/position combination.
Configure the example before connecting a gimbal.

Default test plan
-----------------

The initial configuration runs a four-second test and uses the default position
settling interval:

.. code-block:: python

   TEST_DURATION_SECONDS = MINIMUM_TEST_DURATION_SECONDS
   POSITION_SETTLE_SECONDS = DEFAULT_POSITION_SETTLE_SECONDS

It creates 21 Roll/Pitch positions. Yaw is kept in the controller's normal
home-position stabilization and is not moved by the example:

.. code-block:: python

   POSITIONS = tuple(
       Position(roll, pitch)
       for roll, pitch in product(
           (-30.0, 0.0, 30.0),
           (-90.0, -60.0, -30.0, 0.0, 30.0, 60.0, 90.0),
       )
   )

Axis settings
-------------

Set ``enabled=True`` for every axis that must be tested. Each
``AxisTestSettings`` entry contains independent Bode parameters for its axis:

.. code-block:: python

   AXIS_TESTS = {
       BodeTestAxis.ROLL: AxisTestSettings(True, 3000, 3, 200),
       BodeTestAxis.PITCH: AxisTestSettings(False, 3000, 3, 200),
       BodeTestAxis.YAW: AxisTestSettings(False, 3000, 3, 200),
   }

For each enabled axis, the example commands Roll and Pitch with ``CMD_CONTROL``
and the ``AUTO_TASK`` flag. It waits for the controller completion
confirmation, starts the Bode test, returns Roll and Pitch to neutral, and then
waits one second for recovery.

CSV output
----------

When ``--output-dir`` is omitted, the example opens the native folder-selection
dialog. Files use the following name format:

.. code-block:: text

   <AXIS>_R<roll>_P<pitch>_Y<yaw>.csv

For example, a Roll test at ``R=-30``, ``P=-90`` is saved as
``ROLL_R-30_P-90_Y0.csv``. The script detects duplicate names. Existing files
are offered for replacement unless ``--overwrite`` or ``--no-overwrite`` was
supplied.

Command-line parameters
-----------------------

The example can be started directly from an IDE. With the initial settings it
first asks for a COM port (``7`` is accepted as ``COM7``), then opens the native
folder-selection dialog, and asks before replacing existing CSV files. Command
line keys override these values for one run. Invalid command-line arguments
print the complete ``--help`` reference.

All optional values are kept together at the beginning of the example for easy
adjustment:

.. code-block:: python

   TEST_DURATION_SECONDS = MINIMUM_TEST_DURATION_SECONDS
   POSITION_SETTLE_SECONDS = DEFAULT_POSITION_SETTLE_SECONDS
   WAIT_FOR_AUTO_TASK_CONFIRMATION = True
   SERIAL_PORT: str | None = None
   DEFAULT_OUTPUT_DIR: Path | None = None
   PLOT_ENABLED = False
   PLOT_MODE = "axis"
   OVERWRITE_EXISTING: bool | None = None
   LEAVE_MOTORS_ON = False
   SKIP_START_CONFIRMATION = False

Every optional key overrides its corresponding default for one run:

.. list-table::
   :header-rows: 1

   * - Key
     - Purpose
   * - ``--port COM7``
     - Avoid the COM-port prompt.
   * - ``--output-dir PATH``
     - Avoid the folder-selection dialog.
   * - ``--duration SECONDS``
     - Duration of one test; at least four seconds.
   * - ``--settle-seconds SECONDS``
     - Position settling delay.
   * - ``--axes roll pitch yaw``
     - Restrict the run to axes enabled in ``AXIS_TESTS``.
   * - ``--overwrite`` / ``--no-overwrite``
     - Replace existing CSV files or preserve them without a prompt.
   * - ``--plot`` / ``--no-plot``
     - Enable or disable visualization.
   * - ``--plot-mode axis|file|both``
     - Select grouping of plot windows.
   * - ``--leave-motors-on`` / ``--no-leave-motors-on``
     - Override the motor state after normal completion.
   * - ``--yes``
     - Skip the separate safety confirmation before motion.

Old firmware without ``CMD_CONFIRM``
------------------------------------

By default, ``WAIT_FOR_AUTO_TASK_CONFIRMATION`` is ``True``: before every
test, the example waits for ``CMD_CONFIRM`` after its ``AUTO_TASK`` move. This
is the safest option because it proves that the target position was reached.

Some old firmware versions do not emit this confirmation. If the example
reports an ``AUTO_TASK confirmation was not received`` timeout, change the
setting in the example to ``False`` and use a longer fixed delay, for example:

.. code-block:: python

   WAIT_FOR_AUTO_TASK_CONFIRMATION = False
   POSITION_SETTLE_SECONDS = 5.0

Running safely
--------------

Run the example from the repository root:

.. code-block:: powershell

   python examples/BodeTestAutomation.py --port COM4 --output-dir bode_results --no-plot

The gimbal moves through every configured position. Keep the workspace clear
before confirming the start prompt. Press ``Ctrl+C`` to interrupt the run;
motors are switched off even if ``--leave-motors-on`` was used.

For example, this single run changes only the duration, uses Roll, and
replaces files that already exist:

.. code-block:: powershell

   python examples/BodeTestAutomation.py --port COM4 --output-dir bode_results --axes roll --duration 5 --overwrite --no-plot

Plots
-----

Install optional plotting dependencies:

.. code-block:: powershell

   pip install numpy matplotlib

Use ``--plot`` for one interactive window per tested axis. ``--plot-mode file``
opens a window for each CSV, and ``--plot-mode both`` displays both views. Gain
is shown in blue in dB and phase in red in degrees.
