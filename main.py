from machine import Pin
import time
import config 
from button import Button
from ultrasonic import distance_cm
from motor import setup_motor, duty_from_distance

power_led = Pin(config.POWER_LED_PIN, Pin.OUT)
yolo_led  = Pin(config.YOLO_LED_PIN, Pin.OUT)
power_led.value(0)
yolo_led.value(0)

# hardware connections
# ultrasonic sensor: TRIG drives the pulse, ECHO reads the return
trig  = Pin(config.TRIG_PIN, Pin.OUT)
echo  = Pin(config.ECHO_PIN, Pin.IN)

# button: pull-up means idle=1, pressed=0 (button wired to GND)
btn   = Pin(config.BTN_PIN, Pin.IN, Pin.PULL_UP)

# YOLO button: pull-up means idle=1, pressed=0 (button wired to GND)
yolo_btn = Pin(config.YOLO_PIN, Pin.IN, Pin.PULL_UP)
# vibration motor: PWM lets us "scale" vibration intensity smoothly
motor = setup_motor(Pin(config.MOTOR_PIN))

powered = False
mode    = 0     # 0=standby, 1=vibrate, 2=signal-only

main_button  = Button(
    btn,
    DEBOUNCE_MS=config.DEBOUNCE_MS,
    DOUBLE_CLICK_MS=config.DOUBLE_CLICK_MS,
    LONG_PRESS_MS=config.LONG_PRESS_MS
)
last_dist_ms = 0

# YOLO trigger rate limit
last_yolo_ms = 0
YOLO_COOLDOWN = 2000

yolo_btn_last_val = yolo_btn.value()
yolo_btn_change = time.ticks_ms()

def send_yolo_trigger():
    print("\nYOLO_TRIGGER")
        # Debug: blink YOLO LED for ~0.6s total (3 quick flashes)
    for _ in range(3):
        yolo_led.value(1)
        time.sleep_ms(100)
        yolo_led.value(0)
        time.sleep_ms(100)

def set_mode(new_mode):  # set the operating mode
    global mode
    mode = new_mode

    # always kill vibration when switching modes
    motor.duty_u16(0)

    # user-facing label
    label = ('STANDBY', 'VIBRATE')[new_mode]
    print("\n*** MODE:", label, "***\n")

def power_on():  # power on the device
    global powered
    powered = True
    power_led.value(1)
    set_mode(0)
    print("\n*** POWER ON: STANDBY ***\n")

def power_off():  # power off the device
    global powered
    powered = False
    power_led.value(0)
    yolo_led.value(0)
    set_mode(0)
    print("\n*** POWER OFF ***\n")

def tick_button_b():
    global yolo_btn_last_val, yolo_btn_change

    now = time.ticks_ms()
    val = yolo_btn.value()

    pressed_edge = False
    if val != yolo_btn_last_val and time.ticks_diff(now, yolo_btn_change) > config.DEBOUNCE_MS:
        yolo_btn_change = now
        yolo_btn_last_val = val
        pressed_edge = (val == 0)

    return pressed_edge


# debugging print outs
print("Ready.")
while True:
    # power button and mode selection
    ev = main_button.tick()
    # controls:
    # - long press toggles powher
    # - double click forces standby (if powered)
    # - single click cycles modes (if powered)
    if ev == 'long':
        power_off() if powered else power_on()

    elif powered and ev == 'single':
        # cycle: standby -> vibrate -> signal-only -> vibrate -> ...
        set_mode(1)
        print("\n*** MODE 1: VIBRATE ***\n")

    elif powered and ev == 'double':
        set_mode(0)
        print("\n*** DOUBLE CLICK: STANDBY ***\n")

    # YOLO trigger
    if powered and tick_button_b():
        now = time.ticks_ms()
        if time.ticks_diff(now, last_yolo_ms) >= YOLO_COOLDOWN:
            send_yolo_trigger()
            last_yolo_ms = now


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

    time.sleep_ms(config.LOOP_SLEEP_MS)