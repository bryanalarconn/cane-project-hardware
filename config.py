from micropython import const

DEBUG = True

# pin map:
#   GP0  - UART0 TX  (to Pi 5 RXD, physical pin 10)
#   GP1  - UART0 RX  (from Pi 5 TXD, physical pin 8)
#   GP5  - passive buzzer (PWM audio feedback)
#   GP10 - SW3 momentary button (power on/off, mode select)
#   GP11 - SW4 momentary button (YOLO mode toggle)
#   GP15 - vibration motor (PWM intensity control)
#   GP16 - HC-SR04 ECHO return (digital input)
#   GP17 - HC-SR04 TRIG pulse  (digital output)

BTN_PIN   = const(10)
YOLO_PIN  = const(11)
TRIG_PIN  = const(17)
ECHO_PIN  = const(16)
MOTOR_PIN = const(15)
BUZZER_PIN = const(5)   

# const distance values
# NEAR or closer  = full vibration
# FAR or farther  = motor off
# in between      = linear ramp
NEAR            = const(10)
FAR             = const(75)
LONG_PRESS_MS   = const(3000)
DEBOUNCE_MS     = const(50)
DOUBLE_CLICK_MS = const(400)
LOOP_SLEEP_MS   = const(5)    # fast loop for button responsiveness
DIST_INTERVAL_MS = const(100) # how often to fire the sensor

# buzzer sound definitions
#   SOUND_POWER_ON   - rising chirp when device powers on
#   SOUND_POWER_OFF  - falling chirp when device powers off
#   SOUND_MODE_START - short confirmation when entering a mode
#   SOUND_MODE_STOP  - short confirmation when leaving a mode

#   SOUND_ERROR      - three rapid beeps for self-check failure
 
SOUND_POWER_ON = (
    (800,  120),   # low tone first
    (0,     60),   # gap
    (1600, 180),   # high tone - ascending = powering up
)
 
SOUND_POWER_OFF = (
    (1600, 120),   # high tone first
    (0,     60),   # gap
    (600,  300),   # low tone - descending = powering down
)
 
SOUND_MODE_START = (
    (1000, 80),    # mid tone
    (0,    40),    # gap
    (1400, 80),    # slightly higher - quick "ready" chirp
)
 
SOUND_MODE_STOP = (
    (1400, 80),    # higher tone
    (0,    40),    # gap
    (900,  120),   # lower tone - quick "done" chirp
)
 
SOUND_ERROR = (
    (440, 80),
    (0,   80),
    (440, 80),
    (0,   80),
    (440, 80),     # three rapid beeps
)