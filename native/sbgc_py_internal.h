#ifndef SBGC_PY_INTERNAL_H
#define SBGC_PY_INTERNAL_H

#include <stdint.h>

#include "sbgc32.h"

#ifdef _WIN32
    #ifdef SBGC_PYTHON_EXPORTS
        #define SBGC_PY_API __declspec(dllexport)
    #else
        #define SBGC_PY_API __declspec(dllimport)
    #endif
#else
    #define SBGC_PY_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif


#define SBGC_PY_CONTROL_CONFIRM_ATTEMPTS 3

typedef struct sbgc_py_device sbgc_py_device_t;

int sbgc_py_transport_pop_debug_packet
(
    void *context, ui16 *time_ms, ui8 *port_and_direction, 
    ui8 *command_id, ui8 *payload, ui8 *payload_size
);

void sbgc_py_transport_set_debug_capture_suppressed (void *context, int suppressed);

typedef ui8 (*sbgc_py_tx_callback_t)(void *context, const ui8 *data, ui16 size);
typedef ui8 (*sbgc_py_rx_callback_t)(void *context, ui8 *data);
typedef ui16 (*sbgc_py_available_callback_t)(void *context);
typedef ui32 (*sbgc_py_time_callback_t)(void *context);


typedef enum
{

    SBGC_PY_OK                          = 0,
    SBGC_PY_ERROR                       = -1,
    SBGC_PY_INVALID_ARGUMENT            = -2,
    SBGC_PY_NOT_CONNECTED               = -3,
    SBGC_PY_OPEN_FAILED                 = -4,
    SBGC_PY_COMMUNICATION_ERROR         = -5,
    SBGC_PY_MODULE_DISABLED             = -6,
    SBGC_PY_CONFIRMATION_DISABLED       = -7,
    SBGC_PY_TIMEOUT                     = -8,
    SBGC_PY_EXTERNAL_MOTOR_NO_RESPONSE  = -9,
    SBGC_PY_CAN_NOT_SUPPORTED           = -10,
    SBGC_PY_STATE_VARS_NOT_SUPPORTED    = -11,
    SBGC_PY_IMU_NOT_SUPPORTED           = -12

}   sbgc_py_status_t;


typedef struct
{
    float                       roll,
                                pitch,
                                yaw;

}   sbgc_py_axis3_t;


typedef struct
{
    sbgc_py_axis3_t             imu,
                                target,
                                target_speed;

}   sbgc_py_angles_t;


typedef struct
{
    i16                         imu_angle;
    i16                         target_angle;
    int32_t                     frame_cam_angle;
    ui8                         reserved [10];

}   sbgc_py_axis_gae_t;


typedef struct
{
    sbgc_py_axis_gae_t          axis_gae[ 3];

}   sbgc_py_angles_ext_t;


typedef sbgcScriptDebugInfo_t sbgc_py_script_debug_info_t;
typedef sbgcAutoPID_t sbgc_py_auto_pid_t;
typedef sbgcAxisAPID2_t sbgc_py_auto_pid2_axis_t;
typedef sbgcAutoPID2_t sbgc_py_auto_pid2_t;
typedef sbgcAxisAPIDS_t sbgc_py_auto_pid_axis_state_t;
typedef sbgcAutoPID_State_t sbgc_py_auto_pid_state_t;
typedef sbgcSyncMotors_t sbgc_py_sync_motors_t;
typedef sbgcStateVars_t sbgc_py_state_vars_t;


typedef struct
{
    ui8                         profile_id;
    ui8                         p [3];
    ui8                         i [3];
    ui8                         d [3];

}   sbgc_py_pid_values_t;


typedef struct
{

    ui8                         command_id;
    ui8                         status;
    ui16                        command_data;
    ui8                         error_code;
    ui8                         error_data [4];

}   sbgc_py_confirmation_t;


typedef struct
{
    ui8                         id;
    i32                         value;

}   sbgc_py_adjustable_variable_t;


typedef struct
{
    ui8                         id;
    float                       value;

}   sbgc_py_adjustable_variable_float_t;


typedef struct PACKED__
{
    ui8                         trigger_source;
    ui8                         actions [5];

}   sbgc_py_adjvar_trigger_slot_t;


typedef struct PACKED__
{
    ui8                         source;
    ui8                         variable_id;
    ui8                         min_value;
    ui8                         max_value;

}   sbgc_py_adjvar_analog_slot_t;


typedef struct PACKED__
{
    sbgc_py_adjvar_trigger_slot_t
                                trigger_slots [SBGC_ADJ_VAR_TRIGGER_SLOTS_NUM];

    sbgc_py_adjvar_analog_slot_t
                                analog_slots [SBGC_ADJ_VAR_ANALOG_SLOTS_NUM];

    ui8                         reserved [8];

}   sbgc_py_adjvars_config_t;


typedef struct
{
    ui8                         trigger_slot;
    ui16                        analog_source_id;
    ui8                         analog_variable_id;
    ui16                        lut_source_id;
    ui8                         lut_variable_id;

}   sbgc_py_adjvars_state_request_t;


typedef struct
{
    i16                         trigger_rc_data;
    ui8                         trigger_action;
    i16                         analog_source_value;
    float                       analog_variable_value;
    i16                         lut_source_value;
    float                       lut_variable_value;

}   sbgc_py_adjvars_state_t;


typedef struct
{
    ui8                         id;
    i16                         min_value;
    i16                         max_value;
    i32                         value;

}   sbgc_py_adjvar_info_t;


typedef struct
{
    ui8                         angle_lpf;
    ui8                         speed_lpf;
    ui8                         rc_lpf;
    ui16                        acceleration_limit;
    ui8                         jerk_slope;
    ui8                         reserved;

}   sbgc_py_control_axis_config_t;


typedef struct
{
    ui16                        timeout_ms;
    ui8                         channel_priorities [5];

    sbgc_py_control_axis_config_t
                                axis [3];

    ui8                         rc_expo_rate;
    ui16                        flags;
    ui8                         euler_order;
    ui8                         reserved [9];

}   sbgc_py_control_config_t;


typedef struct PACKED__
{
    ui8                     mode;
    ui8                     flags;
    i32                     speed;
    i32                     angle;

}   sbgc_py_control_ext_axis_t;


typedef struct PACKED__
{
    ui16                        data_set;

    sbgc_py_control_ext_axis_t  axes [3];

}   sbgc_py_control_ext_t;


typedef struct PACKED__
{
    ui8                         mode;
    ui8                         flags;

    float                       attitude [4];
    float                       speed [3];

}   sbgc_py_control_quat_t;


typedef struct PACKED__
{
    ui16                        data_set;
    ui16                        max_speed[3];
    ui16                        acceleration_limit[3];
    ui16                        jerk_slope[3];
    ui16                        flags;
    ui8                         attitude_lpf_frequency;
    ui8                         speed_lpf_frequency;

}   sbgc_py_control_quat_config_t;


typedef struct PACKED__
{
    i32                         setpoint;
    i32                         param1;

}   sbgc_py_ext_motor_control_t;


typedef struct PACKED__
{
    ui8                         motors;
    ui16                        data_set;
    ui8                         mode;
    ui16                        max_speed;
    ui16                        max_acceleration;
    ui16                        jerk_slope;
    ui16                        max_torque;

}   sbgc_py_ext_motors_control_config_t;


typedef sbgcRealTimeData_t sbgc_py_realtime_data_t;


typedef sbgcBoardInfo_t sbgc_py_board_info_t;


typedef struct
{
    ui8                         device_id [9];
    ui8                         mcu_id [12];
    ui32                        eeprom_size;

    ui16                        script_slot_1_size;
    ui16                        script_slot_2_size;
    ui16                        script_slot_3_size;
    ui16                        script_slot_4_size;
    ui16                        script_slot_5_size;

    ui8                         profile_set_slots;
    ui8                         profile_set_current;
    ui8                         flash_size;
    ui8                         imu_calib_info[2];

    ui16                        script_slot_6_size;
    ui16                        script_slot_7_size;
    ui16                        script_slot_8_size;
    ui16                        script_slot_9_size;
    ui16                        script_slot_10_size;

    ui16                        hardware_flags;
    ui32                        board_features_ext2;
    ui8                         can_driver_main_limit;
    ui8                         can_driver_aux_limit;
    ui8                         adjustable_variables_total;

}   sbgc_py_board_info_3_t;


typedef sbgcDataStreamInterval_t sbgc_data_stream_interval_t;

typedef sbgcDebugVar3_Info_t sbgc_debug_var_info_3_t;
typedef sbgcDebugVars3_t sbgc_debug_var_values_3_t;


/* NEED_CONFIRM function */
static inline void sbgc_py_copy_confirmation (sbgc_py_confirmation_t *destination, const sbgcConfirm_t *source)
{
    destination->command_id = source->commandID;
    destination->status = (ui8)source->status;
    destination->command_data = source->cmdData;
    destination->error_code = source->errorCode;

    memcpy(destination->error_data, source->errorData, sizeof(destination->error_data));
}


/*
*   REALTIME MODULE
*/
SBGC_PY_API sbgc_py_status_t sbgc_py_get_angles (sbgc_py_device_t *device, sbgc_py_angles_t *angles);

SBGC_PY_API sbgc_py_status_t sbgc_py_get_angles_ext (sbgc_py_device_t *device, sbgc_py_angles_ext_t *angles);

SBGC_PY_API sbgc_py_status_t sbgc_py_get_realtime_data_3 (sbgc_py_device_t *device, sbgc_py_realtime_data_t *realtime_data);

SBGC_PY_API sbgc_py_status_t sbgc_py_get_realtime_data_4 (sbgc_py_device_t *device, sbgc_py_realtime_data_t *realtime_data);

SBGC_PY_API sbgc_py_status_t sbgc_py_get_realtime_data_custom (sbgc_py_device_t *device, ui32 flags, ui8 *result, ui8 payload_size);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_rc_inputs (sbgc_py_device_t *device, const ui8 *sources, ui8 count, i16 *values);

SBGC_PY_API sbgc_py_status_t sbgc_py_start_data_stream
(
    sbgc_py_device_t *device, const sbgc_data_stream_interval_t *data_stream_interval,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_stop_data_stream
(
    sbgc_py_device_t *device, const sbgc_data_stream_interval_t *data_stream_interval,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_data_stream
(
    sbgc_py_device_t *device, ui8 cmd_id, ui8 *data_straem_struct, ui8 size
);

SBGC_PY_API sbgc_py_status_t sbgc_py_request_debug_var_info_3 
(
    sbgc_py_device_t *device, sbgc_debug_var_info_3_t *debug_var_info_3,
    ui8 statuc_index, ui8 var_count
);

SBGC_PY_API sbgc_py_status_t sbgc_py_request_debug_var_values_3 (sbgc_py_device_t *device, sbgc_debug_var_values_3_t *debug_var_values_3);

SBGC_PY_API sbgc_py_status_t sbgc_py_select_imu_3
(
    sbgc_py_device_t *device, ui8 imu_type, ui8 action, ui16 time_ms,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_control_quat_status
(
    sbgc_py_device_t *device, ui32 flags, ui8 *result, ui8 result_size
);


/*
*   SERVICE MODULE
*/
SBGC_PY_API sbgc_py_status_t sbgc_py_get_board_info (sbgc_py_device_t *device, sbgc_py_board_info_t *board_info);

SBGC_PY_API sbgc_py_status_t sbgc_py_get_board_info_3 (sbgc_py_device_t *device, sbgc_py_board_info_3_t *board_info);

SBGC_PY_API sbgc_py_status_t sbgc_py_reset (sbgc_py_device_t *device, ui8 flags, ui16 delay_ms);

SBGC_PY_API sbgc_py_status_t sbgc_py_expect_reset (sbgc_py_device_t *device);

SBGC_PY_API sbgc_py_status_t sbgc_py_motors_on (sbgc_py_device_t *device);

SBGC_PY_API sbgc_py_status_t sbgc_py_motors_off (sbgc_py_device_t *device, ui8 mode);

SBGC_PY_API sbgc_py_status_t sbgc_py_play_beeper
(
    sbgc_py_device_t *device, ui16 mode, ui8 note_length, 
    ui8 decay_factor, const ui16 *notes_hz, ui8 notes_count
);

SBGC_PY_API sbgc_py_status_t sbgc_py_execute_menu
(
    sbgc_py_device_t *device, ui8 menu_command,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_execute_menu_ext
(
    sbgc_py_device_t *device, ui8 menu_command, ui8 flags,
    sbgc_py_confirmation_t *start_confirmation,
    sbgc_py_confirmation_t *finish_confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_set_trigger_pin
(
    sbgc_py_device_t *device, ui8 pin_id, ui8 state,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_set_servo_out
(
    sbgc_py_device_t *device, const i16 *values, ui8 count
);

SBGC_PY_API sbgc_py_status_t sbgc_py_set_servo_out_ext
(
    sbgc_py_device_t *device, ui32 pins, const i16 *values, ui8 count
);

SBGC_PY_API sbgc_py_status_t sbgc_py_run_script (sbgc_py_device_t *device, ui8 mode, ui8 slot);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_script_debug_info (sbgc_py_device_t *device, sbgc_py_script_debug_info_t *script_debug_info);

SBGC_PY_API sbgc_py_status_t sbgc_py_tune_auto_pid
(
    sbgc_py_device_t *device, const sbgc_py_auto_pid_t *config,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_break_auto_pid (sbgc_py_device_t *device, ui8 need_confirmation, sbgc_py_confirmation_t *confirmation);

SBGC_PY_API sbgc_py_status_t sbgc_py_tune_auto_pid2
(
    sbgc_py_device_t *device, const sbgc_py_auto_pid2_t *config,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_profile_pid_values
(
    sbgc_py_device_t *device, ui8 profile_id, sbgc_py_pid_values_t *values
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_auto_pid_state (sbgc_py_device_t *device, sbgc_py_auto_pid_state_t *state);

SBGC_PY_API sbgc_py_status_t sbgc_py_synchronize_motors
(
    sbgc_py_device_t *device, const sbgc_py_sync_motors_t *config,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_request_motor_state
(
    sbgc_py_device_t *device, ui8 motor_id, ui32 data_set,
    ui8 *result, ui16 size
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_motor_state (sbgc_py_device_t *device, ui8 *result, ui16 size);

SBGC_PY_API sbgc_py_status_t sbgc_py_set_boot_mode
(
    sbgc_py_device_t *device, ui8 extended,
    ui8 need_confirmation, ui16 delay_ms
);

SBGC_PY_API sbgc_py_status_t sbgc_py_write_state_vars
(
    sbgc_py_device_t *device, const sbgc_py_state_vars_t *state,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_state_vars
(
    sbgc_py_device_t *device, sbgc_py_state_vars_t *state
);

SBGC_PY_API sbgc_py_status_t sbgc_py_set_debug_port
(
    sbgc_py_device_t *device, ui8 action, ui32 filter,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_debug_port
(
    sbgc_py_device_t *device, ui16 *time_ms, ui8 *port_and_direction,
    ui8 *command_id, ui8 *payload, ui8 *payload_size, ui16 payload_capacity
);

SBGC_PY_API sbgc_py_status_t sbgc_py_request_module_list
(
    sbgc_py_device_t *device, sbgcCAN_ModuleInfo_t *CAN_module_info, ui8 device_num_max
);

SBGC_PY_API sbgc_py_status_t sbgc_py_CAN_device_scan (sbgc_py_device_t *device, sbgcCAN_DeviceScan_t *CAN_device_scan);

SBGC_PY_API sbgc_py_status_t sbgc_py_sign_message
(
    sbgc_py_device_t *device, ui8 sign_type,
    const ui8 tx_message [SBGC_MAX_MESSAGE_LENGTH], ui8 rx_message [SBGC_MAX_MESSAGE_LENGTH]
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_transparent_command (sbgc_py_device_t *device, sbgcTransparentCommand_t *cmd);

SBGC_PY_API sbgc_py_status_t sbgc_py_send_transparent_command (sbgc_py_device_t *device, const sbgcTransparentCommand_t *cmd);


/* 
*   EERPROM MODULE
*/
SBGC_PY_API sbgc_py_status_t sbgc_py_read_i2c_reg
(
    sbgc_py_device_t *device, ui8 device_addr, ui8 register_addr,
    ui8 size, ui8 *result
);

SBGC_PY_API sbgc_py_status_t sbgc_py_write_i2c_reg
(
    sbgc_py_device_t *device, ui8 device_addr, ui8 register_addr,
    const ui8 *data, ui8 size, ui8 need_confirmation,
    sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_eeprom
(
    sbgc_py_device_t *device, ui32 address, ui16 size, ui8 *result
);

SBGC_PY_API sbgc_py_status_t sbgc_py_write_eeprom
(
    sbgc_py_device_t *device, ui32 address, const ui8 *data, ui16 size,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_external_data (sbgc_py_device_t *device, ui8 *result);

SBGC_PY_API sbgc_py_status_t sbgc_py_write_external_data
(
    sbgc_py_device_t *device, const ui8 *data, ui8 need_confirmation,
    sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_file
(
    sbgc_py_device_t *device, ui16 file_id, ui16 page_offset, ui16 max_size,
    ui8 *data, ui16 *file_size, ui16 *result_page_offset, ui8 *error_code
);

SBGC_PY_API sbgc_py_status_t sbgc_py_write_file
(
    sbgc_py_device_t *device, ui16 file_id, ui16 page_offset,
    const ui8 *data, ui16 size, ui8 need_confirmation,
    sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_clear_file_system (sbgc_py_device_t *device);


/*
*   PROFILES MODULE
*/
SBGC_PY_API sbgc_py_status_t sbgc_py_read_profile_names (sbgc_py_device_t *device, ui8 *names, ui16 size);

SBGC_PY_API sbgc_py_status_t sbgc_py_write_profile_names
(
    sbgc_py_device_t *device, const ui8 *names, ui16 size,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_manage_profile_set
(
    sbgc_py_device_t *device, ui8 slot, ui8 action,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_write_params_set
(
    sbgc_py_device_t *device, ui8 action,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_profile_params
(
    sbgc_py_device_t *device, ui8 block, ui8 profile_id, ui8 *result, ui16 size
);

SBGC_PY_API sbgc_py_status_t sbgc_py_write_profile_params
(
    sbgc_py_device_t *device, ui8 block, const ui8 *data, ui16 size,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_use_profile_defaults (sbgc_py_device_t *device, ui8 profile_id);


/* 
*   IMU MODULE 
*/
SBGC_PY_API sbgc_py_status_t sbgc_py_request_ext_imu_debug
(
    sbgc_py_device_t *device, ui8 *result, ui8 size
);

SBGC_PY_API sbgc_py_status_t sbgc_py_send_ext_imu_command
(
    sbgc_py_device_t *device, ui8 *command_id, ui8 *payload,
    ui8 payload_size, ui8 command_type
);

SBGC_PY_API sbgc_py_status_t sbgc_py_send_ext_sens_command
(
    sbgc_py_device_t *device, ui8 *command_id, ui8 *payload,
    ui8 payload_size, ui8 flags, ui8 command_type
);

SBGC_PY_API sbgc_py_status_t sbgc_py_correction_gyro
(
    sbgc_py_device_t *device, ui8 imu_type, const i16 *zero_correction,
    i16 zero_heading_correction
);

SBGC_PY_API sbgc_py_status_t sbgc_py_call_ahrs_helper
(
    sbgc_py_device_t *device, ui8 *helper, ui8 size, ui16 mode
);

SBGC_PY_API sbgc_py_status_t sbgc_py_provide_helper_data
(
    sbgc_py_device_t *device, const ui8 *helper_data, ui8 size
);

SBGC_PY_API sbgc_py_status_t sbgc_py_provide_helper_data_ext
(
    sbgc_py_device_t *device, const ui8 *helper_data, ui8 size
);
  

/*
*   CALIB MODULE
*/
SBGC_PY_API sbgc_py_status_t sbgc_py_calib_acc (sbgc_py_device_t *device);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_gyro (sbgc_py_device_t *device);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_mag (sbgc_py_device_t *device);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_acc_ext 
(
    sbgc_py_device_t *device, sbgcIMU_ExtCalib_t *IMU_ExtCalib, 
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_gyro_ext 
(
    sbgc_py_device_t *device, sbgcIMU_ExtCalib_t *IMU_ExtCalib, 
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_mag_ext
(
    sbgc_py_device_t *device, sbgcIMU_ExtCalib_t *IMU_ExtCalib, 
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_request_calib_info (sbgc_py_device_t *device, sbgcCalibInfo_t *calib_info, ui8 imu_type);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_encoders_offset (sbgc_py_device_t *device, sbgcCalibParameter_t forMotor);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_encoders_fld_offset (sbgc_py_device_t *device);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_encoders_fld_offset_ext (sbgc_py_device_t *device, const sbgcCalibEncodersOffset_t *calib_encoders_offset);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_poles (sbgc_py_device_t *device);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_offset (sbgc_py_device_t *device);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_bat (sbgc_py_device_t *device, ui16 voltage, ui8 need_confirmation, sbgc_py_confirmation_t *confirmation);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_orient_corr (sbgc_py_device_t *device, ui8 need_confirmation, sbgc_py_confirmation_t *confirmation);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_acc_ext_ref 
(
    sbgc_py_device_t *device, const i16 accRef [3], 
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_calib_cogging
(
    sbgc_py_device_t *device, const ui8 *data, ui8 size,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);


/*
*   GIMBAL CONTROL MODULE
*/
SBGC_PY_API sbgc_py_status_t sbgc_py_set_api_virtual_channels (sbgc_py_device_t *device, const i16 *API_virt_ch, ui8 ch_quan);

SBGC_PY_API sbgc_py_status_t sbgc_py_control
(
    sbgc_py_device_t *device, const ui8 modes [3], const i16 speeds [3], const i16 angles [3],
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_control_config
(
    sbgc_py_device_t *device,
    const sbgc_py_control_config_t *config,
    ui8 need_confirmation,
    sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_control_ext (sbgc_py_device_t *device, const sbgc_py_control_ext_t *control);

SBGC_PY_API sbgc_py_status_t sbgc_py_control_quat
(
    sbgc_py_device_t *device, const sbgc_py_control_quat_t *control,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_control_quat_config
(
    sbgc_py_device_t *device, const sbgc_py_control_quat_config_t *config,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_ext_motors_action
(
    sbgc_py_device_t *device, ui8 motors, ui8 action,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_ext_motors_control
(
    sbgc_py_device_t *device, const sbgc_py_ext_motor_control_t *control,
    ui8 motors, ui8 data_set, ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_ext_motors_control_config
(
    sbgc_py_device_t *device, const sbgc_py_ext_motors_control_config_t *config,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_set_api_virtual_channels_hr
(
    sbgc_py_device_t *device, const i16 *channels, ui8 count
);


/*
*   ADJVAR MODULE
*/
SBGC_PY_API sbgc_py_status_t sbgc_py_get_adj_vars (sbgc_py_device_t *device, const ui8 *ids, ui8 count, sbgc_py_adjustable_variable_t *result);

SBGC_PY_API sbgc_py_status_t sbgc_py_set_adj_vars 
(
    sbgc_py_device_t *device, const sbgc_py_adjustable_variable_t *variables,
    ui8 count, ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_save_adj_vars 
(
    sbgc_py_device_t *device, const ui8 *ids, ui8 count, 
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_get_adj_vars_float (sbgc_py_device_t *device, const ui8 *ids, ui8 count, sbgc_py_adjustable_variable_float_t *result);

SBGC_PY_API sbgc_py_status_t sbgc_py_set_adj_vars_float
(
    sbgc_py_device_t *device, const sbgc_py_adjustable_variable_float_t *variables,
    ui8 count, ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_adj_vars_config (sbgc_py_device_t *device, sbgc_py_adjvars_config_t *config);

SBGC_PY_API sbgc_py_status_t sbgc_py_write_adj_vars_config
(
    sbgc_py_device_t *device, const sbgc_py_adjvars_config_t *config,
    ui8 need_confirmation, sbgc_py_confirmation_t *confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_get_adj_vars_state
(
    sbgc_py_device_t *device, const sbgc_py_adjvars_state_request_t *request,
    sbgc_py_adjvars_state_t *result
);

SBGC_PY_API sbgc_py_status_t sbgc_py_get_adj_vars_info
(
    sbgc_py_device_t *device, ui8 start_id, sbgc_py_adjvar_info_t *result,
    ui8 capacity, ui8 *count
);


/*
*   TRANSPORT MODULE
*/
SBGC_PY_API sbgc_py_device_t *sbgc_py_open
(
    void *context, sbgc_py_tx_callback_t transmit, sbgc_py_rx_callback_t receive_byte,
    sbgc_py_available_callback_t available_bytes, sbgc_py_time_callback_t get_time_ms
);

SBGC_PY_API sbgc_py_device_t *sbgc_py_open_com (const char *port, ui32 baudrate);

SBGC_PY_API void sbgc_py_close (sbgc_py_device_t *device);

SBGC_PY_API sbgc_py_status_t sbgc_py_recover (sbgc_py_device_t *device);

SBGC_PY_API sbgc_py_status_t sbgc_py_get_last_error (sbgc_py_device_t *device, int *error);

struct sbgc_py_device
{
    void                            *context;
    sbgc_py_tx_callback_t           transmit;
    sbgc_py_rx_callback_t           receive_byte;

    sbgc_py_available_callback_t    available_bytes;
    sbgc_py_time_callback_t         get_time_ms;

    sbgcGeneral_t                   serial_api;

    int                             connected;

    void (*close_context)(void *context);
    void (*recover_context)(void *context);

};

extern sbgc_py_device_t *current_device;

#ifdef __cplusplus
}
#endif

#endif
