from enum import IntEnum

class Command(IntEnum):
    CMD_BOARD_INFO              = 86    # Request board and firmware information +
    CMD_BOARD_INFO_3            = 20    # Request additional board information +

    CMD_SAVE_PARAMS_3           = 32    # Saves current values of parameters linked to adjustable variables in EEPROM
    CMD_RUN_SCRIPT              = 57    # Start or stop user-written script +
    CMD_EXECUTE_MENU            = 69    # Execute menu command

    CMD_REALTIME_DATA           = 68    # Request real-time data !
    CMD_REALTIME_DATA_3         = 23    # Request real-time data +
    CMD_REALTIME_DATA_4         = 25    # Receive extended version of real-time data +
    CMD_REALTIME_DATA_CUSTOM    = 88    # Request configurable realtime data
    
    CMD_GET_ANGLES              = 73    # Request information related to IMU angles and RC control state +
    CMD_GET_ANGLES_EXT          = 61    # Request information related to IMU angles and RC control state +

    CMD_SET_ADJ_VARS_VAL        = 31    # Update the value of selected parameter(-s)
    CMD_GET_ADJ_VARS_VAL        = 64    # Query the actual value of selected parameter(-s)

    CMD_MOTORS_ON               = 77    # Switch motors ON
    CMD_MOTORS_OFF              = 109   # Switch motors OFF
    
    CMD_BEEP_SOUND              = 89    # Play melody by motors or emit standard beep sound
    CMD_CONTROL_CONFIG          = 90    # Configure the handling of CMD_CONTROL command
    
    CMD_CONFIRM                 = 67    # Confirmation of previous command or finished calibration
    CMD_CONTROL                 = 67    # Controls gimbal movement
    CMD_RESET                   = 114   # Tx: reset device / Rx: notification on device reset +
    CMD_ERROR                   = 255   # Error executing previous command
