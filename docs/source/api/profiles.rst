Profile commands
================

The profiles module reads and writes profile names and parameter blocks,
manages profile sets, and controls profile-writing mode. Read operations return
names, raw parameter bytes or ``ProfileParameters``; writes return ``None`` or
a requested confirmation.

.. autofunction:: sbgc32.modules.profiles.read_profile_names
.. autofunction:: sbgc32.modules.profiles.write_profile_names
.. autofunction:: sbgc32.modules.profiles.manage_profile_set
.. autofunction:: sbgc32.modules.profiles.set_profile_writing
.. autofunction:: sbgc32.modules.profiles.read_profile_parameter_block
.. autofunction:: sbgc32.modules.profiles.write_profile_parameter_block
.. autofunction:: sbgc32.modules.profiles.read_params_3
.. autofunction:: sbgc32.modules.profiles.read_params_ext
.. autofunction:: sbgc32.modules.profiles.read_params_ext2
.. autofunction:: sbgc32.modules.profiles.read_params_ext3
.. autofunction:: sbgc32.modules.profiles.write_params_3
.. autofunction:: sbgc32.modules.profiles.write_params_ext
.. autofunction:: sbgc32.modules.profiles.write_params_ext2
.. autofunction:: sbgc32.modules.profiles.write_params_ext3
.. autofunction:: sbgc32.modules.profiles.read_profile_parameters
.. autofunction:: sbgc32.modules.profiles.write_profile_parameters
.. autofunction:: sbgc32.modules.profiles.use_profile_defaults
