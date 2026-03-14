from machine import Pin
import time
import config 
from button import Button
from ultrasonic import distance_cm
from motor import setup_motor, duty_from_distance
from buzzer import power_on_sound, power_off_sound 


power_led = Pin(config.POWER_LED_PIN, Pin.OUT)
power_led.value(0)

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

buzzer_pin = Pin(config.BUZZER_PIN, Pin.OUT)   # <-- ADD THIS


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

yolo_button = Button(
    yolo_btn,
    DEBOUNCE_MS=config.DEBOUNCE_MS,
    DOUBLE_CLICK_MS=config.DOUBLE_CLICK_MS,
    LONG_PRESS_MS=config.LONG_PRESS_MS
)

def send_yolo_trigger():
    print("\nYOLO_TRIGGER")


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
    power_on_sound(buzzer_pin) 
    set_mode(0)
    print("\n*** POWER ON: STANDBY ***\n")

def power_off():  # power off the device
    global powered
    motor.duty_u16(0)             # stop motor before shutdown
    power_off_sound(buzzer_pin)
    powered = False
    power_led.value(0)
    set_mode(0)
    print("\n*** POWER OFF ***\n")

def safe_shutdown():
    global powered
    print("\n*** SAFE SHUTDOWN TRIGGERED ***\n")
    # 1. Stop motor immediately - safety first
    motor.duty_u16(0)

    # 2. Audible + visual feedback so user knows shutdown is happening
    power_off_sound(buzzer_pin)
    power_led.value(0)

    # 3. Signal the Raspberry Pi to shut down gracefully
    #    Pi's mode2.py reads this line and can call `sudo shutdown -h now`
    print("SHUTDOWN_TRIGGER")

    # 4. Update state
    powered = False
    mode    = 0

    print("*** PICO IDLE - WAITING FOR POWER CYCLE ***\n")

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
    b2_ev = yolo_button.tick()

    if powered and b2_ev == 'single':
        now = time.ticks_ms()
        if time.ticks_diff(now, last_yolo_ms) >= YOLO_COOLDOWN:
            send_yolo_trigger()
            last_yolo_ms = now

    elif b2_ev == 'double':
        safe_shutdown()


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