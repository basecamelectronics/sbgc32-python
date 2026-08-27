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

    SBGC_PY_OK                  = 0,
    SBGC_PY_ERROR               = -1,
    SBGC_PY_INVALID_ARGUMENT    = -2,
    SBGC_PY_NOT_CONNECTED       = -3,
    SBGC_PY_OPEN_FAILED         = -4,
    SBGC_PY_COMMUNICATION_ERROR = -5,
    SBGC_PY_MODULE_DISABLED     = -6,
    SBGC_PY_CONFIRMATION_DISABLED = -7

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
    i16                     imu_angle;
    i16                     target_angle;
    int32_t                     frame_cam_angle;
    ui8                     reserved[10];

}   sbgc_py_axis_gae_t;


typedef struct
{
    sbgc_py_axis_gae_t          axis_gae[3];

}   sbgc_py_angles_ext_t;


typedef struct
{
    ui16                    current_command_counter;
    ui8                     error_code;

}   sbgc_py_script_debug_info_t;


#pragma pack(push, 1)
typedef struct
{
    ui8 profile_id;
    ui8 config_flags;
    ui8 gain_vs_stability;
    ui8 momentum;
    ui8 action;
    ui8 reserved[14];

}   sbgc_py_auto_pid_t;


typedef struct
{
    ui8 axis_flags;
    ui8 gain;
    ui16 stimulus_gain;
    ui8 effective_frequency;
    ui8 problem_frequency;
    ui8 problem_margin;
    ui8 reserved[6];

}   sbgc_py_auto_pid2_axis_t;


typedef struct
{
    ui8 action;
    ui16 command_flags;
    ui8 reserved1[8];
    ui8 config_version;
    sbgc_py_auto_pid2_axis_t axis[3];
    ui16 general_flags;
    ui8 reserved3;
    ui8 test_frequency_from;
    ui8 test_frequency_to;
    ui8 multi_position_flags;
    int8_t multi_position_angle[4];
    ui8 reserved4[12];
}   sbgc_py_auto_pid2_t;


typedef struct
{
    float tracking_error;
    ui8 reserved[6];
}   sbgc_py_auto_pid_axis_state_t;


typedef struct
{
    ui8 p[3];
    ui8 i[3];
    ui8 d[3];
    ui16 lpf_frequency[3];
    ui16 iteration_count;
    sbgc_py_auto_pid_axis_state_t axis[3];
    ui8 reserved[10];
}   sbgc_py_auto_pid_state_t;
#pragma pack(pop)


typedef struct
{
    ui8 axis;
    ui8 power;
    ui16 time_ms;
    ui16 angle;
}   sbgc_py_sync_motors_t;


#pragma pack(push, 1)
typedef struct
{
    ui8 step_signal_vars[6];
    ui8 sub_error;
    ui8 max_acc;
    ui32 work_time;
    ui16 startup_count;
    ui16 max_current;
    ui8 imu_temp_min;
    ui8 imu_temp_max;
    ui8 mcu_temp_min;
    ui8 mcu_temp_max;
    ui8 shock_count[4];
    ui32 energy_time;
    float energy;
    ui32 avg_current_time;
    float avg_current;
    ui8 reserved[152];
}   sbgc_py_state_vars_t;
#pragma pack(pop)


typedef struct
{

    ui8                     command_id;
    ui8                     status;
    ui16                    command_data;
    ui8                     error_code;
    ui8                     error_data[4];

}   sbgc_py_confirmation_t;


typedef struct
{
    ui8                     id;
    i32                     value;

}   sbgc_py_adjustable_variable_t;


typedef struct
{
    ui8                     angle_lpf;
    ui8                     speed_lpf;
    ui8                     rc_lpf;
    ui16                    acceleration_limit;
    ui8                     jerk_slope;
    ui8                     reserved;

}   sbgc_py_control_axis_config_t;


typedef struct
{
    ui16                    timeout_ms;
    ui8                     channel_priorities[5];
    sbgc_py_control_axis_config_t
                                axis[3];
    ui8                     rc_expo_rate;
    ui16                    flags;
    ui8                     euler_order;
    ui8                     reserved[9];

}   sbgc_py_control_config_t;


typedef struct
{
    i16                     acc_data;
    i16                     gyro_data;

}   sbgc_py_axis_rtd_t;


typedef struct
{
    sbgc_py_axis_rtd_t          axis_rtd[3];
    ui16                    serial_error_count;
    ui16                    system_error;
    ui8                     system_sub_error;
    ui8                     reserved[3];
    i16                     rc_roll;
    i16                     rc_pitch;
    i16                     rc_yaw;
    i16                     rc_cmd;
    i16                     ext_fc_roll;
    i16                     ext_fc_pitch;
    i16                     imu_angle[3];
    i16                     frame_imu_angle[3];
    i16                     target_angle[3];
    ui16                    cycle_time;
    ui16                    i2c_error_count;
    ui8                     error_code;
    ui16                    bat_level;
    ui8                     rt_data_flags;
    ui8                     cur_imu;
    ui8                     cur_profile;
    ui8                     motor_power[3];
    i16                     frame_cam_angle[3];
    ui8                     reserved1;
    i16                     balance_error[3];
    ui16                    current;
    i16                     mag_data[3];
    int8_t                      imu_temperature;
    int8_t                      frame_imu_temperature;
    ui8                     imu_g_error;
    ui8                     imu_h_error;
    i16                     motor_out[3];
    ui8                     calib_mode;
    ui8                     can_imu_ext_sens_error;
    i16                     actual_angle[3];
    ui32                    system_state_flags;
    ui8                     reserved2[18];

}   sbgc_py_realtime_data_t;


typedef struct
{
    ui8                     board_ver;
    ui16                    firmware_ver;
    ui8                     state_flags;
    ui16                    board_features;
    ui8                     connection_flag;
    ui32                    firmware_extra_id;
    ui16                    board_features_ext;
    ui8                     main_imu_sensor_model;
    ui8                     frame_imu_sensor_model;
    ui8                     build_number;
    ui16                    base_firmware_ver;

}   sbgc_py_board_info_t;



typedef struct
{
    ui8                     device_id [9];
    ui8                     mcu_id [12];
    ui32                    eeprom_size;

    ui16                    script_slot_1_size;
    ui16                    script_slot_2_size;
    ui16                    script_slot_3_size;
    ui16                    script_slot_4_size;
    ui16                    script_slot_5_size;

    ui8                     profile_set_slots;
    ui8                     profile_set_current;
    ui8                     flash_size;
    ui8                     imu_calib_info[2];

    ui16                    script_slot_6_size;
    ui16                    script_slot_7_size;
    ui16                    script_slot_8_size;
    ui16                    script_slot_9_size;
    ui16                    script_slot_10_size;

    ui16                        hardware_flags;
    ui32                        board_features_ext2;
    ui8                         can_driver_main_limit;
    ui8                         can_driver_aux_limit;
    ui8                         adjustable_variables_total;

}   sbgc_py_board_info_3_t;


#pragma pack(push, 1)
typedef struct
{
    ui8                         cmd_id;

    ui16                        interval_ms;

    ui8                         config [8],
                                sync_to_data,
                                reserved [9];

}   sbgc_data_stream_interval_t;
#pragma pack(pop)

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
    sbgc_py_device_t* device, const sbgc_data_stream_interval_t* data_stream_interval,
    ui8 need_confirmation, sbgc_py_confirmation_t* confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_stop_data_stream
(
    sbgc_py_device_t* device, const sbgc_data_stream_interval_t* data_stream_interval,
    ui8 need_confirmation, sbgc_py_confirmation_t* confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_data_stream
(
    sbgc_py_device_t* device, ui8 cmd_id, ui8* data_straem_struct, ui8 size
);

SBGC_PY_API sbgc_py_status_t sbgc_py_request_debug_var_info_3 
(
    sbgc_py_device_t* device, sbgc_debug_var_info_3_t *debug_var_info_3,
    ui8 statuc_index, ui8 var_count
);

SBGC_PY_API sbgc_py_status_t sbgc_py_request_debug_var_values_3 (sbgc_py_device_t* device, sbgc_debug_var_values_3_t* debug_var_values_3);

SBGC_PY_API sbgc_py_status_t sbgc_py_select_imu_3
(
    sbgc_py_device_t* device, ui8 imu_type, ui8 action, ui16 time_ms,
    ui8 need_confirmation, sbgc_py_confirmation_t* confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_control_quat_status
(
    sbgc_py_device_t* device, ui32 flags, ui8* result, ui8 result_size
);


/*
*   SERVICE MODULE
*/
SBGC_PY_API sbgc_py_status_t sbgc_py_get_board_info (sbgc_py_device_t *device, sbgc_py_board_info_t *board_info);

SBGC_PY_API sbgc_py_status_t sbgc_py_get_board_info_3 (sbgc_py_device_t *device, sbgc_py_board_info_3_t *board_info);

SBGC_PY_API sbgc_py_status_t sbgc_py_reset (sbgc_py_device_t *device, ui8 flags, ui16 delay_ms);

SBGC_PY_API sbgc_py_status_t sbgc_py_expect_reset (sbgc_py_device_t *device);

SBGC_PY_API sbgc_py_status_t sbgc_py_motors_on (sbgc_py_device_t* device);

SBGC_PY_API sbgc_py_status_t sbgc_py_motors_off (sbgc_py_device_t* device, ui8 mode);

SBGC_PY_API sbgc_py_status_t sbgc_py_play_beeper
(
    sbgc_py_device_t* device, ui16 mode, ui8 note_length, 
    ui8 decay_factor, const ui16* notes_hz, ui8 notes_count
);

SBGC_PY_API sbgc_py_status_t sbgc_py_execute_menu
(
    sbgc_py_device_t* device, ui8 menu_command,
    ui8 need_confirmation, sbgc_py_confirmation_t* confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_run_script (sbgc_py_device_t* device, ui8 mode, ui8 slot);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_script_debug_info (sbgc_py_device_t* device, sbgc_py_script_debug_info_t* script_debug_info);

SBGC_PY_API sbgc_py_status_t sbgc_py_tune_auto_pid
(
    sbgc_py_device_t* device, const sbgc_py_auto_pid_t* config,
    ui8 need_confirmation, sbgc_py_confirmation_t* confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_break_auto_pid (sbgc_py_device_t* device, ui8 need_confirmation, sbgc_py_confirmation_t* confirmation);

SBGC_PY_API sbgc_py_status_t sbgc_py_tune_auto_pid2
(
    sbgc_py_device_t* device, const sbgc_py_auto_pid2_t* config,
    ui8 need_confirmation, sbgc_py_confirmation_t* confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_auto_pid_state (sbgc_py_device_t* device, sbgc_py_auto_pid_state_t* state);

SBGC_PY_API sbgc_py_status_t sbgc_py_synchronize_motors
(
    sbgc_py_device_t* device, const sbgc_py_sync_motors_t* config,
    ui8 need_confirmation, sbgc_py_confirmation_t* confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_request_motor_state
(
    sbgc_py_device_t* device, ui8 motor_id, ui32 data_set,
    ui8* result, ui16 size
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_motor_state (sbgc_py_device_t* device, ui8* result, ui16 size);

SBGC_PY_API sbgc_py_status_t sbgc_py_set_boot_mode
(
    sbgc_py_device_t* device, ui8 extended,
    ui8 need_confirmation, ui16 delay_ms
);

SBGC_PY_API sbgc_py_status_t sbgc_py_write_state_vars
(
    sbgc_py_device_t* device, const sbgc_py_state_vars_t* state,
    ui8 need_confirmation, sbgc_py_confirmation_t* confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_state_vars
(
    sbgc_py_device_t* device, sbgc_py_state_vars_t* state
);

SBGC_PY_API sbgc_py_status_t sbgc_py_set_debug_port
(
    sbgc_py_device_t* device, ui8 action, ui32 filter,
    ui8 need_confirmation, sbgc_py_confirmation_t* confirmation
);

SBGC_PY_API sbgc_py_status_t sbgc_py_read_debug_port
(
    sbgc_py_device_t* device, ui16* time_ms, ui8* port_and_direction,
    ui8* command_id, ui8* payload, ui16 payload_capacity
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


/*
*   TRANSPORT MODULE
*/
SBGC_PY_API sbgc_py_device_t* sbgc_py_open
(
    void* context, sbgc_py_tx_callback_t transmit, sbgc_py_rx_callback_t receive_byte,
    sbgc_py_available_callback_t available_bytes, sbgc_py_time_callback_t get_time_ms
);

SBGC_PY_API sbgc_py_device_t* sbgc_py_open_com (const char* port, ui32 baudrate);

SBGC_PY_API void sbgc_py_close (sbgc_py_device_t* device);

SBGC_PY_API sbgc_py_status_t sbgc_py_recover (sbgc_py_device_t* device);

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
