#ifndef SBGC_PYTHON_H
#define SBGC_PYTHON_H

#include <stdint.h>

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

typedef struct sbgc_py_device sbgc_py_device_t;


typedef uint8_t (*sbgc_py_tx_callback_t)(
    void *context,
    const uint8_t *data,
    uint16_t size
);


typedef uint8_t (*sbgc_py_rx_callback_t)(void *context, uint8_t *data);
typedef uint16_t (*sbgc_py_available_callback_t)(void *context);
typedef uint32_t (*sbgc_py_time_callback_t)(void *context);


typedef enum
{

    SBGC_PY_OK                  = 0,
    SBGC_PY_ERROR               = -1,
    SBGC_PY_INVALID_ARGUMENT    = -2,
    SBGC_PY_NOT_CONNECTED       = -3,
    SBGC_PY_OPEN_FAILED         = -4,
    SBGC_PY_COMMUNICATION_ERROR = -5,
    /* The SerialAPI module required by the requested command is disabled
       in serialAPI_Config.h. */
    SBGC_PY_MODULE_DISABLED     = -6,
    /* CMD_CONFIRM handling was requested but SBGC_NEED_CONFIRM_CMD is off. */
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
    /* Mirrors sbgcAxisGAE_t from modules/realtime/realtime.h. */
    int16_t                     imu_angle;
    int16_t                     target_angle;
    int32_t                     frame_cam_angle;
    uint8_t                     reserved[10];

}   sbgc_py_axis_gae_t;


typedef struct
{
    /* Mirrors sbgcGetAnglesExt_t.AxisGAE[3] (roll, pitch, yaw). */
    sbgc_py_axis_gae_t          axis_gae[3];

}   sbgc_py_angles_ext_t;


typedef struct
{
    /* Mirrors sbgcScriptDebugInfo_t from modules/service/service.h. */
    uint16_t                    current_command_counter;
    uint8_t                     error_code;

}   sbgc_py_script_debug_info_t;


typedef struct
{
    /* A portable snapshot of sbgcConfirm_t after CMD_CONFIRM or CMD_ERROR. */
    uint8_t                     command_id;
    uint8_t                     status;
    uint16_t                    command_data;
    uint8_t                     error_code;
    uint8_t                     error_data[4];

}   sbgc_py_confirmation_t;


/* Wire-level integer adjustable variable used by CMD_SET/GET_ADJ_VARS_VAL. */
typedef struct
{
    uint8_t                     id;
    int32_t                     value;

}   sbgc_py_adjustable_variable_t;


/* Mirrors sbgcAxisCCtrl_t / sbgcControlConfig_t without SerialAPI-private
   field names. All zero values retain the board defaults for the corresponding
   optional control settings. */
typedef struct
{
    uint8_t                     angle_lpf;
    uint8_t                     speed_lpf;
    uint8_t                     rc_lpf;
    uint16_t                    acceleration_limit;
    uint8_t                     jerk_slope;
    uint8_t                     reserved;

}   sbgc_py_control_axis_config_t;


typedef struct
{
    uint16_t                    timeout_ms;
    uint8_t                     channel_priorities[5];
    sbgc_py_control_axis_config_t
                                axis[3];
    uint8_t                     rc_expo_rate;
    uint16_t                    flags;
    uint8_t                     euler_order;
    uint8_t                     reserved[9];

}   sbgc_py_control_config_t;


typedef struct
{
    int16_t                     acc_data;
    int16_t                     gyro_data;

}   sbgc_py_axis_rtd_t;


/* Mirrors sbgcRealTimeData_t from modules/realtime/realtime.h. */
typedef struct
{
    sbgc_py_axis_rtd_t          axis_rtd[3];
    uint16_t                    serial_error_count;
    uint16_t                    system_error;
    uint8_t                     system_sub_error;
    uint8_t                     reserved[3];
    int16_t                     rc_roll;
    int16_t                     rc_pitch;
    int16_t                     rc_yaw;
    int16_t                     rc_cmd;
    int16_t                     ext_fc_roll;
    int16_t                     ext_fc_pitch;
    int16_t                     imu_angle[3];
    int16_t                     frame_imu_angle[3];
    int16_t                     target_angle[3];
    uint16_t                    cycle_time;
    uint16_t                    i2c_error_count;
    uint8_t                     error_code;
    uint16_t                    bat_level;
    uint8_t                     rt_data_flags;
    uint8_t                     cur_imu;
    uint8_t                     cur_profile;
    uint8_t                     motor_power[3];
    int16_t                     frame_cam_angle[3];
    uint8_t                     reserved1;
    int16_t                     balance_error[3];
    uint16_t                    current;
    int16_t                     mag_data[3];
    int8_t                      imu_temperature;
    int8_t                      frame_imu_temperature;
    uint8_t                     imu_g_error;
    uint8_t                     imu_h_error;
    int16_t                     motor_out[3];
    uint8_t                     calib_mode;
    uint8_t                     can_imu_ext_sens_error;
    int16_t                     actual_angle[3];
    uint32_t                    system_state_flags;
    uint8_t                     reserved2[18];

}   sbgc_py_realtime_data_t;


typedef struct
{
    uint8_t                     board_ver;
    uint16_t                    firmware_ver;
    uint8_t                     state_flags;
    uint16_t                    board_features;
    uint8_t                     connection_flag;
    uint32_t                    firmware_extra_id;
    uint16_t                    board_features_ext;
    uint8_t                     main_imu_sensor_model;
    uint8_t                     frame_imu_sensor_model;
    uint8_t                     build_number;
    uint16_t                    base_firmware_ver;

}   sbgc_py_board_info_t;



typedef struct
{
    uint8_t device_id[9];
    uint8_t mcu_id[12];
    uint32_t eeprom_size;

    uint16_t script_slot_1_size;
    uint16_t script_slot_2_size;
    uint16_t script_slot_3_size;
    uint16_t script_slot_4_size;
    uint16_t script_slot_5_size;

    uint8_t profile_set_slots;
    uint8_t profile_set_current;
    uint8_t flash_size;
    uint8_t imu_calib_info[2];

    uint16_t script_slot_6_size;
    uint16_t script_slot_7_size;
    uint16_t script_slot_8_size;
    uint16_t script_slot_9_size;
    uint16_t script_slot_10_size;

    uint16_t hardware_flags;
    uint32_t board_features_ext2;
    uint8_t can_driver_main_limit;
    uint8_t can_driver_aux_limit;
    uint8_t adjustable_variables_total;

} sbgc_py_board_info_3_t;


SBGC_PY_API sbgc_py_device_t *sbgc_py_open(
    void *context,
    sbgc_py_tx_callback_t transmit,
    sbgc_py_rx_callback_t receive_byte,
    sbgc_py_available_callback_t available_bytes,
    sbgc_py_time_callback_t get_time_ms
);

/* Optional Windows-only native COM transport. The Python package uses pyserial callbacks. */
SBGC_PY_API sbgc_py_device_t *sbgc_py_open_com (const char *port, uint32_t baudrate);

SBGC_PY_API void sbgc_py_close (sbgc_py_device_t *device);

/* Clears pending serial input and recreates the Serial API parser after a failed exchange. */
SBGC_PY_API sbgc_py_status_t sbgc_py_recover (sbgc_py_device_t *device);

/* functions that call SBGC32 function */
SBGC_PY_API sbgc_py_status_t sbgc_py_get_angles (sbgc_py_device_t *device, sbgc_py_angles_t *angles);
SBGC_PY_API sbgc_py_status_t sbgc_py_get_angles_ext (sbgc_py_device_t *device, sbgc_py_angles_ext_t *angles);
SBGC_PY_API sbgc_py_status_t sbgc_py_get_board_info (sbgc_py_device_t *device, sbgc_py_board_info_t *board_info);
SBGC_PY_API sbgc_py_status_t sbgc_py_get_board_info_3 (sbgc_py_device_t *device, sbgc_py_board_info_3_t *board_info);
/* Send CMD_RESET, then optionally wait for its CMD_RESET notification. */
SBGC_PY_API sbgc_py_status_t sbgc_py_reset (sbgc_py_device_t *device, uint8_t flags, uint16_t delay_ms);
SBGC_PY_API sbgc_py_status_t sbgc_py_expect_reset (sbgc_py_device_t *device);
/* Switch motors on, or switch them off using sbgcMotorsMode_t (0..2).
   The bridge deliberately uses SBGC_NO_CONFIRM: these functions report
   successful transmission, not the board's asynchronous CMD_CONFIRM packet. */
SBGC_PY_API sbgc_py_status_t sbgc_py_motors_on (sbgc_py_device_t *device);
SBGC_PY_API sbgc_py_status_t sbgc_py_motors_off (sbgc_py_device_t *device, uint8_t mode);
/* Send the 15-byte CMD_CONTROL payload. No confirmation is expected here. */
SBGC_PY_API sbgc_py_status_t sbgc_py_control (
    sbgc_py_device_t *device,
    const uint8_t modes[3],
    const int16_t speeds[3],
    const int16_t angles[3],
    uint8_t need_confirmation,
    sbgc_py_confirmation_t *confirmation
);
SBGC_PY_API sbgc_py_status_t sbgc_py_control_config (
    sbgc_py_device_t *device,
    const sbgc_py_control_config_t *config,
    uint8_t need_confirmation,
    sbgc_py_confirmation_t *confirmation
);
/* ``variables`` and ``result`` must have ``count`` entries; count is 1..40. */
SBGC_PY_API sbgc_py_status_t sbgc_py_get_adj_vars (
    sbgc_py_device_t *device,
    const uint8_t *ids,
    uint8_t count,
    sbgc_py_adjustable_variable_t *result
);
SBGC_PY_API sbgc_py_status_t sbgc_py_set_adj_vars (
    sbgc_py_device_t *device,
    const sbgc_py_adjustable_variable_t *variables,
    uint8_t count,
    uint8_t need_confirmation,
    sbgc_py_confirmation_t *confirmation
);
/* CMD_SAVE_PARAMS_3. ``count`` is 1..102 for selected IDs; zero saves all
   active adjustable variables. */
SBGC_PY_API sbgc_py_status_t sbgc_py_save_adj_vars (
    sbgc_py_device_t *device,
    const uint8_t *ids,
    uint8_t count,
    uint8_t need_confirmation,
    sbgc_py_confirmation_t *confirmation
);
SBGC_PY_API sbgc_py_status_t sbgc_py_run_script (sbgc_py_device_t *device, uint8_t mode, uint8_t slot);
SBGC_PY_API sbgc_py_status_t sbgc_py_read_script_debug_info (
    sbgc_py_device_t *device, sbgc_py_script_debug_info_t *script_debug_info
);
SBGC_PY_API sbgc_py_status_t sbgc_py_get_realtime_data_3 (
    sbgc_py_device_t *device, sbgc_py_realtime_data_t *realtime_data
);
SBGC_PY_API sbgc_py_status_t sbgc_py_get_realtime_data_4 (
    sbgc_py_device_t *device, sbgc_py_realtime_data_t *realtime_data
);
/* ``result`` must provide at least ``payload_size + 4`` bytes. The bridge
   stores the request flags in result[0..3]; SerialAPI writes the received
   CMD_REALTIME_DATA_CUSTOM payload at result + 4. */
SBGC_PY_API sbgc_py_status_t sbgc_py_get_realtime_data_custom (
    sbgc_py_device_t *device, uint32_t flags, uint8_t *result, uint8_t payload_size
);

/* Diagnostic snapshots of the most recent command exchange. */
SBGC_PY_API uint16_t sbgc_py_copy_last_tx (sbgc_py_device_t *device, uint8_t *buffer, uint16_t capacity);
SBGC_PY_API uint16_t sbgc_py_copy_last_rx (sbgc_py_device_t *device, uint8_t *buffer, uint16_t capacity);

#ifdef __cplusplus
}
#endif

#endif
