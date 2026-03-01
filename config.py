from micropython import const


# GPIO pins that we are using
BTN_PIN   = const(10)
YOLO_PIN  = const(11)
TRIG_PIN  = const(17)
ECHO_PIN  = const(16)
MOTOR_PIN = const(15)

# const distance values
NEAR            = const(10)
FAR             = const(75)
LONG_PRESS_MS   = const(3000)
DEBOUNCE_MS     = const(50)
DOUBLE_CLICK_MS = const(400)
LOOP_SLEEP_MS   = const(5)    # fast loop for button responsiveness
DIST_INTERVAL_MS = const(100) # how often to fire the sensor


