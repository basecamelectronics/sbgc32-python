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

Choose an output directory interactively or supply ``--output-dir``. Files use
the following name format:

.. code-block:: text

   <AXIS>_R<roll>_P<pitch>_Y<yaw>.csv

For example, a Roll test at ``R=-30``, ``P=-90`` is saved as
``ROLL_R-30_P-90_Y0.csv``. The script detects duplicate names and asks before
replacing existing files unless ``--overwrite`` was supplied.

Running safely
--------------

Run the example from the repository root:

.. code-block:: powershell

   python examples/BodeTestAutomation.py --port COM4 --output-dir bode_results

The gimbal moves through every configured position. Keep the workspace clear
before confirming the start prompt. Press ``Ctrl+C`` to interrupt the run;
motors are switched off even if ``--leave-motors-on`` was used.

Add ``--no-plot`` to skip the visualization question and run without plots:

.. code-block:: powershell

   python examples/BodeTestAutomation.py --port COM4 --output-dir bode_results --no-plot

Plots
-----

Install optional plotting dependencies:

.. code-block:: powershell

   pip install numpy matplotlib

Use ``--plot`` for one interactive window per tested axis. ``--plot-mode file``
opens a window for each CSV, and ``--plot-mode both`` displays both views. Gain
is shown in blue in dB and phase in red in degrees.
