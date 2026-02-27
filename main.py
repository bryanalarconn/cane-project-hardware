from machine import Pin
import time
import config 
from button import Button
from ultrasonic import distance_cm
from motor import setup_motor, duty_from_distance

# hardware connections
# ultrasonic sensor: TRIG drives the pulse, ECHO reads the return
trig  = Pin(config.TRIG_PIN, Pin.OUT)
echo  = Pin(config.ECHO_PIN, Pin.IN)

# button: pull-up means idle=1, pressed=0 (button wired to GND)
btn   = Pin(config.BTN_PIN, Pin.IN, Pin.PULL_UP)

# vibration motor: PWM lets us "scale" vibration intensity smoothly
motor = setup_motor(Pin(config.MOTOR_PIN))

powered = False
mode    = 0     # 0=standby, 1=vibrate, 2=signal-only
button  = Button(
    btn,
    DEBOUNCE_MS=config.DEBOUNCE_MS,
    DOUBLE_CLICK_MS=config.DOUBLE_CLICK_MS,
    LONG_PRESS_MS=config.LONG_PRESS_MS
)
last_dist_ms = 0

def set_mode(new_mode):  # set the operating mode
    global mode
    mode = new_mode

    # always kill vibration when switching modes
    motor.duty_u16(0)

    # user-facing label
    label = ('STANDBY', 'VIBRATE', 'SIGNAL ONLY')[new_mode]
    print("\n*** MODE:", label, "***\n")

def power_on():  # power on the device
    global powered
    powered = True
    set_mode(0)
    print("\n*** POWER ON: STANDBY ***\n")

def power_off():  # power off the device
    global powered
    powered = False
    set_mode(0)
    print("\n*** POWER OFF ***\n")

# debugging print outs
print("Ready.")
while True:
    ev = button.tick()

    # controls:
    # - long press toggles power
    # - double click forces standby (if powered)
    # - single click cycles modes (if powered)
    if ev == 'long':
        power_off() if powered else power_on()

    elif ev == 'double':
        if powered:
            set_mode(0)
            print("\n*** DOUBLE CLICK: STANDBY ***\n")

    elif ev == 'single':
        if powered:
            # cycle: standby -> vibrate -> signal-only -> vibrate -> ...
            if mode == 0:
                set_mode(1)
                print("\n*** MODE 1: VIBRATE ***\n")
            elif mode == 1:
                set_mode(2)
                print("\n*** MODE 2: SIGNAL ONLY ***\n")
            else:
                set_mode(1)
                print("\n*** MODE 1: VIBRATE ***\n")

    # motor / sensor logic
    # standby = motor off + skip sensor reads
    if not powered or mode == 0:
        motor.duty_u16(0)
        time.sleep_ms(config.LOOP_SLEEP_MS)
        continue

    # fire the sensor at a fixed interval, independent of the fast button loop
    now = time.ticks_ms()
    if time.ticks_diff(now, last_dist_ms) >= config.DIST_INTERVAL_MS:
        last_dist_ms = now

        # blocking ~0.6–30ms depending on distance/timeout; fine at 100ms intervals
        d = distance_cm(trig, echo)

        if mode == 1:
            # MODE 1: vibrate intensity scales with distance
            if d is None:
                motor.duty_u16(0)
                print("Mode 1 | dist: None | duty: 0")
            else:
                duty = duty_from_distance(d, config.NEAR, config.FAR)
                motor.duty_u16(duty)
                print("Mode 1 | dist:", round(d, 1), "cm | duty:", duty)

        elif mode == 2:
            # MODE 2: signal-only (no vibration)
            # confirm can be used later as a boolean trigger for other logic
            motor.duty_u16(0)

            if d is None:
                confirm = False
            else:
                confirm = (d <= config.FAR)

            # right now we just print distance; confirm is computed for later use
            print("Mode 2 | dist:", (round(d, 1) if d is not None else None),
                  "cm")

    time.sleep_ms(config.LOOP_SLEEP_MS)