Realtime and stream commands
============================

The realtime module reads orientation, realtime controller state, RC inputs,
quaternion status, debug variables and controller data streams. Results are
decoded value objects; malformed controller payloads raise ``ValueError`` in
the decoder, while a missing response raises ``CommandTimeoutError``.

.. autofunction:: sbgc32.modules.realtime.get_angles
.. autofunction:: sbgc32.modules.realtime.get_angles_ext
.. autofunction:: sbgc32.modules.realtime.get_realtime_data
.. autofunction:: sbgc32.modules.realtime.get_realtime_data_3
.. autofunction:: sbgc32.modules.realtime.get_realtime_data_4
.. autofunction:: sbgc32.modules.realtime.get_realtime_data_custom
.. autofunction:: sbgc32.modules.realtime.get_realtime_data_custom2
.. autofunction:: sbgc32.modules.realtime.parse_realtime_data_custom
.. autofunction:: sbgc32.modules.realtime.parse_realtime_data_custom2
.. autofunction:: sbgc32.modules.realtime.realtime_data_custom_payload_size
.. autofunction:: sbgc32.modules.realtime.realtime_data_custom2_payload_size
.. autofunction:: sbgc32.modules.realtime.read_rc_inputs
.. autofunction:: sbgc32.modules.realtime.get_control_quat_status
.. autofunction:: sbgc32.modules.realtime.start_data_stream
.. autofunction:: sbgc32.modules.realtime.stop_data_stream
.. autofunction:: sbgc32.modules.realtime.read_data_stream
.. autofunction:: sbgc32.modules.realtime.request_debug_var_info_3
.. autofunction:: sbgc32.modules.realtime.request_debug_var_values_3
.. autofunction:: sbgc32.modules.realtime.select_imu_3
