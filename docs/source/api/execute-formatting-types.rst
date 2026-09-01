Execute and formatting data types
=================================

.. py:class:: sbgc32.Command

   Enum of controller commands that can be passed to ``execute`` when that
   command has an implemented typed-method mapping. It does not describe the
   required arguments; use :doc:`the execute guide <../execute-formatting>`.

.. py:class:: sbgc32.ResponseCommand

   Enum of packets sent by the controller. These values are responses, not
   requests, and cannot be passed to ``execute``.

.. py:class:: sbgc32.CommandConfirmation

   Returned by selected commands when ``need_confirmation=True``.

   .. list-table::
      :header-rows: 1
      :widths: 30 25 45

      * - Field
        - Type
        - Meaning
      * - ``command_id``
        - ``int``
        - Confirmed command identifier.
      * - ``status``
        - ``int``
        - Firmware confirmation status.
      * - ``command_data`` / ``error_code`` / ``error_data``
        - protocol values
        - Optional command and error details supplied by the firmware.
