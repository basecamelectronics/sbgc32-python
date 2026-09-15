Value types and enums
=====================

``sbgc32.types`` contains every public value class and enumeration. Import the
module once when namespacing is preferred:

.. code-block:: python

   from sbgc32 import types

   control_mode = types.ControlMode.ANGLE
   axis = types.Axis3(roll=0, pitch=0, yaw=0)

The same namespace is available on a connection as ``gimbal.types``. Value
classes carry command input or decoded controller data; enums provide the
named numeric values defined by SerialAPI. Constructing a value class performs
no serial I/O.

Public classes and enums
------------------------

.. automodule:: sbgc32.types
   :members:
   :show-inheritance:
