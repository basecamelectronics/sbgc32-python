Adjustable variables
====================

This module reads, writes and persists integer and floating-point adjustable
variables, their mapping configuration, current state and metadata. Read
operations return decoded variable objects; write and save operations return
``None`` or a requested confirmation.

.. autofunction:: sbgc32.modules.adjvars.get_adj_vars
.. autofunction:: sbgc32.modules.adjvars.get_adj_var
.. autofunction:: sbgc32.modules.adjvars.set_adj_vars
.. autofunction:: sbgc32.modules.adjvars.set_adj_var
.. autofunction:: sbgc32.modules.adjvars.save_adj_vars
.. autofunction:: sbgc32.modules.adjvars.save_all_adj_vars
.. autofunction:: sbgc32.modules.adjvars.get_adj_vars_float
.. autofunction:: sbgc32.modules.adjvars.get_adj_var_float
.. autofunction:: sbgc32.modules.adjvars.set_adj_vars_float
.. autofunction:: sbgc32.modules.adjvars.set_adj_var_float
.. autofunction:: sbgc32.modules.adjvars.read_adj_vars_config
.. autofunction:: sbgc32.modules.adjvars.write_adj_vars_config
.. autofunction:: sbgc32.modules.adjvars.get_adj_vars_state
.. autofunction:: sbgc32.modules.adjvars.get_adj_vars_info
