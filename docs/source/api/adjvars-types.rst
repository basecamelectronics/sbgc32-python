Adjustable-variable data types
==============================

The following structures are used by the adjustable-variables API.

Variable values
---------------

.. py:class:: sbgc32.AdjustableVariable

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``id``
        - ``int``
        - Adjustable-variable identifier.
      * - ``value``
        - ``int``
        - Signed 32-bit raw value.

.. py:class:: sbgc32.AdjustableVariableFloat

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``id``
        - ``int``
        - Adjustable-variable identifier.
      * - ``value``
        - ``float``
        - Floating-point value.

Configuration
-------------

.. py:class:: sbgc32.TriggerSlot

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``source``
        - ``int``
        - Firmware trigger source.
      * - ``actions``
        - ``tuple[int, int, int, int, int]``
        - Five actions attached to the source.

.. py:class:: sbgc32.AnalogSlot

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``source``
        - ``int``
        - Firmware analog source.
      * - ``variable_id``
        - ``int``
        - Controlled variable identifier.
      * - ``min_value`` / ``max_value``
        - ``int``
        - Value range mapped from the analog source.

.. py:class:: sbgc32.AdjustableVariablesConfig

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``trigger_slots``
        - ``tuple[TriggerSlot, ...]``
        - Trigger-slot configuration.
      * - ``analog_slots``
        - ``tuple[AnalogSlot, ...]``
        - Analog-slot configuration.
      * - ``reserved``
        - ``bytes``
        - Reserved protocol bytes; preserve when rewriting a read value.

Runtime and metadata
--------------------

.. py:class:: sbgc32.AdjustableVariablesState

   .. list-table::
      :header-rows: 1
      :widths: 34 20 46

      * - Field
        - Type
        - Meaning
      * - ``trigger_rc_data`` / ``trigger_action``
        - ``int``
        - Current trigger input and action.
      * - ``analog_source_value`` / ``analog_variable_value``
        - ``int`` / ``float``
        - Current analog source and mapped variable values.
      * - ``lut_source_value`` / ``lut_variable_value``
        - ``int`` / ``float``
        - Current lookup-table source and mapped variable values.

.. py:class:: sbgc32.AdjustableVariableInfo

   .. list-table::
      :header-rows: 1
      :widths: 25 25 50

      * - Field
        - Type
        - Meaning
      * - ``id``
        - ``int``
        - Variable identifier.
      * - ``min_value`` / ``max_value``
        - ``int``
        - Firmware-defined valid range.
      * - ``value``
        - ``int``
        - Current value.
