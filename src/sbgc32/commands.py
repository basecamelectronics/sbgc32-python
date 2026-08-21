from enum import IntEnum


class Command(IntEnum):
    """ List of commands send to th board. """

    # Device information
    CMD_BOARD_INFO              = 86    # Request board and firmware information
    CMD_BOARD_INFO_3            = 20    # Request additional board information

    # Real-time state monitoring and diagnostics
    CMD_REALTIME_DATA_CUSTOM    = 88    # Request configurable realtime data
    CMD_REALTIME_DATA           = 22    # Request real-time data
    CMD_REALTIME_DATA_3         = 23    # Request real-time data
    CMD_REALTIME_DATA_4         = 25    # Receive extended version of real-time data
    CMD_GET_ANGLES              = 73    # Request information related to IMU angles and RC control state
    CMD_GET_ANGLES_EXT          = 61    # Request information related to IMU angles and RC control state

    # Run-time gimbal parameters
    CMD_SAVE_PARAMS_3           = 32    # Saves current values of parameters linked to adjustable variables in EEPROM
    CMD_SET_ADJ_VARS_VAL        = 31    # Update the value of selected parameter(-s)
    CMD_GET_ADJ_VARS_VAL        = 64    # Query the actual value of selected parameter(-s)

    # Controlling gimbal movements
    CMD_CONTROL                 = 67    # Send 15-byte gimbal movement command
    CMD_CONTROL_CONFIG          = 90    # Configure the handling of CMD_CONTROL command

    # Miscellaneous commands
    CMD_RESET                   = 114   # Tx: reset device / Rx: notification on device reset
    CMD_MOTORS_ON               = 77    # Switch motors ON
    CMD_MOTORS_OFF              = 109   # Switch motors OFF
    CMD_EXECUTE_MENU            = 69    # Execute menu command
    CMD_RUN_SCRIPT              = 57    # Start or stop user-written script
    CMD_BEEP_SOUND              = 89    # Play melody by motors or emit standard beep sound


class ResponseCommand(IntEnum):
    """ Commands that are sent by the board and must not be passed to execute. """

    CMD_CONFIRM                 = 67    # Confirmation of a previous command
    CMD_ERROR                   = 255   # Error executing a previous command


class MenuCommands(IntEnum):
    """ Special codes for menu commands. """

    MENU_CMD_NO                         = 0
    MENU_CMD_PROFILE1                   = 1
    MENU_CMD_PROFILE2                   = 2
    MENU_CMD_PROFILE3                   = 3
    # MENU_CMD_SWAP_PITCH_ROLL    = 4
    # MENU_CMD_SWAP_YAW_ROLL      = 5
    # MENU_CMD_CALIB_ACC          = 6
    # MENU_CMD_RESET              = 7
    # MENU_CMD_SET_ANGLE          = 8
    # MENU_CMD_CALIB_GYRO         = 9
    # MENU_CMD_MOTOR_TOGGLE       = 10
    MENU_CMD_MOTOR_ON                   = 11
    MENU_CMD_MOTOR_OFF                  = 12
    # MENU_CMD_FRAME_UPSIDE_DOWN  = 13
    MENU_CMD_PROFILE4                   = 14
    MENU_CMD_PROFILE5                   = 15
    # MENU_CMD_AUTO_PID           = 16
    # MENU_CMD_LOOK_DOWN          = 17
    MENU_CMD_HOME_POSITION              = 18
    # MENU_CMD_RC_BIND            = 19
    # MENU_CMD_CALIB_GYRO_TEMP    = 20
    # MENU_CMD_CALIB_ACC_TEMP     = 21
    # MENU_CMD_BUTTON_PRESS       = 22
    MENU_CMD_RUN_SCRIPT1                = 23
    MENU_CMD_RUN_SCRIPT2                = 24
    MENU_CMD_RUN_SCRIPT3                = 25
    MENU_CMD_RUN_SCRIPT4                = 26
    MENU_CMD_RUN_SCRIPT5                = 27
    # MENU_CMD_CALIB_MAG          = 33
    # MENU_CMD_LEVEL_ROLL_PITCH   = 34
    MENU_CMD_CENTER_YAW                 = 35
    # MENU_CMD_UNTWIST_CABLES     = 36
    # MENU_CMD_SET_ANGLE_NO_SAVE  = 37
    # MENU_CMD_HOME_POSITION_SHORTEST = 38
    # MENU_CMD_CENTER_YAW_SHORTEST = 39
    # MENU_CMD_ROTATE_YAW_180     = 40
    # MENU_CMD_ROTATE_YAW_180_FRAME_REL = 41
    # MENU_CMD_SWITCH_YAW_180_FRAME_REL = 42
    # MENU_CMD_SWITCH_POS_ROLL_90 = 43
    # MENU_CMD_START_TIMELAPSE = 44
    # MENU_CMD_CALIB_MOMENTUM = 45
    # MENU_CMD_LEVEL_ROLL = 46
    # MENU_CMD_REPEAT_TIMELAPSE = 47
    # MENU_CMD_LOAD_PROFILE_SET1 = 48
    # MENU_CMD_LOAD_PROFILE_SET2 = 49
    # MENU_CMD_LOAD_PROFILE_SET3 = 50
    # MENU_CMD_LOAD_PROFILE_SET4 = 51
    # MENU_CMD_LOAD_PROFILE_SET5 = 52
    # MENU_CMD_LOAD_PROFILE_SET_BACKUP = 53
    # MENU_CMD_INVERT_RC_ROLL = 54
    # MENU_CMD_INVERT_RC_PITCH = 55
    # MENU_CMD_INVERT_RC_YAW = 56
    # MENU_CMD_SNAP_TO_FIXED_POSITION = 57
    # MENU_CMD_CAMERA_REC_PHOTO_EVENT = 58
    # MENU_CMD_CAMERA_PHOTO_EVENT = 59
    MENU_CMD_MOTORS_SAFE_STOP           = 60
    # MENU_CMD_CALIB_ACC_AUTO = 61
    # MENU_CMD_RESET_IMU = 62
    # MENU_CMD_FORCED_FOLLOW_TOGGLE = 63
    # MENU_CMD_AUTO_PID_GAIN_ONLY = 64
    # MENU_CMD_LEVEL_PITCH = 65
    # MENU_CMD_MOTORS_SAFE_TOGGLE = 66
    # MENU_CMD_TIMELAPSE_STEP1 = 67
    # MENU_CMD_EXT_GYRO_ONLINE_CALIB = 68
    # MENU_CMD_DISABLE_FOLLOW_TOGGLE = 69
    # MENU_CMD_SET_CUR_POS_AS_HOME = 70
    MENU_CMD_STOP_SCRIPT                = 71
    # MENU_CMD_TRIPOD_MODE_OFF = 72
    # MENU_CMD_TRIPOD_MODE_ON = 73
    # MENU_CMD_SET_RC_TRIM = 74
    # MENU_CMD_HOME_POSITION_MOTORS = 75
    # MENU_CMD_RETRACTED_POSITION = 76
    # MENU_CMD_SHAKE_GENERATOR_OFF = 77
    # MENU_CMD_SHAKE_GENERATOR_ON = 78
    # MENU_CMD_SERVO_MODE_ON = 79
    # MENU_CMD_SERVO_MODE_OFF = 80
    # MENU_CMD_SERVO_MODE_TOGGLE = 81