from machine import Pin
import time
import config 
from button import Button
from ultrasonic import distance_cm
from motor import setup_motor, duty_from_distance
from buzzer import power_on_sound, power_off_sound 


# all pins declared upfront so wiring is easy to audit in one place

power_led = Pin(config.POWER_LED_PIN, Pin.OUT)
power_led.value(0) # LED off until device is on (testing)

trig  = Pin(config.TRIG_PIN, Pin.OUT) # TRIG drives the pulse,
echo  = Pin(config.ECHO_PIN, Pin.IN) #  ECHO reads the return

btn   = Pin(config.BTN_PIN, Pin.IN, Pin.PULL_UP) # main button (button 1)
yolo_btn = Pin(config.YOLO_PIN, Pin.IN, Pin.PULL_UP) # YOLO button (button 2)
motor = setup_motor(Pin(config.MOTOR_PIN)) # PWM so we can  scale vibration intensity

buzzer_pin = Pin(config.BUZZER_PIN, Pin.OUT)   # passive buzzer for audio feedback

 # button objects 
main_button  = Button(
    btn,
    DEBOUNCE_MS=config.DEBOUNCE_MS,
    DOUBLE_CLICK_MS=config.DOUBLE_CLICK_MS,
    LONG_PRESS_MS=config.LONG_PRESS_MS
)
yolo_button = Button(
    yolo_btn,
    DEBOUNCE_MS=config.DEBOUNCE_MS,
    DOUBLE_CLICK_MS=config.DOUBLE_CLICK_MS,
    LONG_PRESS_MS=config.LONG_PRESS_MS
)

# state variables
powered = False
mode    = 0     # 0=standby, 1=vibrate

last_dist_ms = 0 # tracks when we last fired the distance sensor
last_yolo_ms = 0 # tracks when we last sent a YOLO trigger

YOLO_COOLDOWN = 2000 # ms between YOLO triggers


# helper functions
def send_yolo_trigger():
    print("\nYOLO_TRIGGER")

def send_yolo_stop():
    print("\nYOLO_STOP")
    print("*** YOLO STOPPED ***\n")


def set_mode(new_mode):  # set the operating mode
    # always kill vibration when switching modes
    global mode
    mode = new_mode
    motor.duty_u16(0)

    label = ('STANDBY', 'VIBRATE')[new_mode]
    print("\n*** MODE:", label, "***\n")

def power_on():  # power on the device
    global powered
    powered = True
    power_led.value(1)
    power_on_sound(buzzer_pin) # audio cue to show device is on
    set_mode(0)
    print("\n*** POWER ON: STANDBY ***\n")

def power_off():  # power off the device
    global powered
    motor.duty_u16(0) # stop motor before shutdown
    power_off_sound(buzzer_pin)
    powered = False
    power_led.value(0)
    set_mode(0)
    print("\n*** POWER OFF ***\n")

# button controls
#   main button  | long press   -> toggle power on/off
#   main button  | single click -> mode 1 (vibrate)
#   main button  | double click -> standby
#   yolo button  | single click -> start YOLO model
#   yolo button  | double click -> stop YOLO model
def main():
    print("Ready.")
    while True:
        global last_yolo_ms, last_dist_ms
        # main button
        ev = main_button.tick()
        if ev == 'long':
            power_off() if powered else power_on()

        elif powered and ev == 'single':
            set_mode(1)
            print("\n*** MODE 1: VIBRATE ***\n")

        elif powered and ev == 'double':
            set_mode(0)
            print("\n*** DOUBLE CLICK: STANDBY ***\n")

        # YOLO button
        ev2 = yolo_button.tick()

        if powered and ev2 == 'single':
            now = time.ticks_ms() 
            if time.ticks_diff(now, last_yolo_ms) >= YOLO_COOLDOWN:
                send_yolo_trigger()
                last_yolo_ms = now

        elif powered and ev2 == 'double':
            send_yolo_stop()        # stop the model, device stays on


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
                # vibration intensity scales with distance
                if d is None:
                    motor.duty_u16(0)
                    print("dist: None | duty: 0")
                else:
                    duty = duty_from_distance(d, config.NEAR, config.FAR)
                    motor.duty_u16(duty)
                    print("dist:", round(d, 1), "cm | duty:", duty)

        time.sleep_ms(config.LOOP_SLEEP_MS)

if __name__ == "__main__":
    main()