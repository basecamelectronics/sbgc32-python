Profiles
========

Profiles contain controller settings. Profile names are convenient metadata;
parameter blocks are raw firmware data and should normally be copied from a
known compatible controller or stored unchanged.

.. code-block:: python

   names = gimbal.read_profile_names()
   print(gimbal.format_profile_names(names))

   parameters = gimbal.read_profile_parameters()
   # Store or compare the four raw blocks before writing them elsewhere.

Writing all profile parameters automatically brackets the individual writes
with the controller's profile-writing mode. Restoring defaults and clearing a
profile-set slot require ``confirm=True``.

.. seealso::

   :doc:`Profiles API reference <api/profiles>`
