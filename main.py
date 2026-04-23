from machine import Pin, UART
import time
import config
from drivers.button import Button
from drivers.ultrasonic import distance_cm
from drivers.motor import setup_motor, duty_from_distance
from drivers.buzzer import (power_on_sound, power_off_sound,
                            mode_start_sound, mode_stop_sound, error_sound)
from debug import dbg
from selfcheck import run_selfcheck

# all pins declared upfront so wiring is easy to audit in one place
trig  = Pin(config.TRIG_PIN, Pin.OUT)   # TRIG drives the pulse
echo  = Pin(config.ECHO_PIN, Pin.IN)    # ECHO reads the return

btn      = Pin(config.BTN_PIN, Pin.IN, Pin.PULL_UP)   # power/mode
yolo_btn = Pin(config.YOLO_PIN, Pin.IN, Pin.PULL_UP)  # YOLO toggle

motor      = setup_motor(Pin(config.MOTOR_PIN))  # PWM for vibration intensity
buzzer_pin = Pin(config.BUZZER_PIN, Pin.OUT)      # buzzer for audio feedback

# UART to Pi - GP0 (TX) -> Pi pin 10 (RXD), GP1 (RX) -> Pi pin 8 (TXD)
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))


# Button objects 
main_button = Button(
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

STATE_OFF     = 0
STATE_STANDBY = 1
STATE_MODE1   = 2
STATE_MODE2   = 3

_STATE_NAMES = {0: "OFF", 1: "STANDBY", 2: "MODE1-SONAR", 3: "MODE2-YOLO"}


state = STATE_OFF
last_dist_ms = 0


# Commands to Pi
# sent over UART; mode2.py on Pi reads these lines
def send_yolo_trigger():
    uart.write(b'YOLO_TRIGGER\n')
    dbg("UART TX -> YOLO_TRIGGER")
    
def send_yolo_stop():
    uart.write(b'YOLO_STOP\n')
    dbg("UART TX -> YOLO_STOP")


def _log_state_transition(new_state):
    dbg("STATE: {} -> {}".format(
        _STATE_NAMES.get(state, "?"),
        _STATE_NAMES.get(new_state, "?")))

# State transitions

def _announce(new_state):
    dbg("STATE: {} → {}".format(
        _STATE_NAMES.get(state, "?"),
        _STATE_NAMES.get(new_state, "?")))
 
def enter_off():
    global state, motor
    _announce(STATE_OFF)
    motor.duty_u16(0)
    motor.deinit()                 # fully release motor PWM before buzzer plays
    power_off_sound(buzzer_pin)
    # reinit motor so it's ready if device powers back on
    motor = setup_motor(Pin(config.MOTOR_PIN))
    state = STATE_OFF
 
def enter_standby():
    global state, motor
    _announce(STATE_STANDBY)
    # setup_motor() starts at duty 0 so motor is off
    motor = setup_motor(Pin(config.MOTOR_PIN))
    state = STATE_STANDBY
 
def enter_mode1():
    global state
    _announce(STATE_MODE1)
    mode_start_sound(buzzer_pin)   # quick ascending "ready" chirp
    state = STATE_MODE1
 
def enter_mode2():
    global state
    _announce(STATE_MODE2)
    send_yolo_trigger()
    mode_start_sound(buzzer_pin)   # quick ascending "ready" chirp
    state = STATE_MODE2
 
def exit_mode1():
    """stop sonar and return to standby"""
    dbg("Exiting Mode 1")
    mode_stop_sound(buzzer_pin)    
    motor.duty_u16(0)
    motor.deinit()                 # fully release motor PWM before buzzer plays
    enter_standby()
 
def exit_mode2():
    dbg("Exiting Mode 2")
    send_yolo_stop()
    mode_stop_sound(buzzer_pin)    
    enter_standby()
 
def full_power_off():
    dbg("Full power-off requested")
    if state == STATE_MODE2:
        send_yolo_stop()
    elif state == STATE_MODE1:
        # motor PWM is active in Mode 1, release it before buzzer plays
        motor.duty_u16(0)
        motor.deinit()
    enter_off()

# Main loop 

def main():
    global last_dist_ms
    
    ok = run_selfcheck()
    if not ok:
        dbg("Self-check warnings")
    else:
        dbg("Self-check passed")

    dbg("Pico ready. System OFF. Pi idle in background.")

    while True:
        ev1 = main_button.tick()
        ev2 = yolo_button.tick()
        now = time.ticks_ms()

        # STATE: OFF 
        if state == STATE_OFF:
            if ev1 == 'long':
                power_on_sound(buzzer_pin)
                enter_standby()

        # STATE: STANDBY
        elif state == STATE_STANDBY:
            if ev1 == 'long':
                full_power_off()

            elif ev1 == 'single':
                enter_mode1()

            elif ev2 == 'long':
                enter_mode2()

        # STATE: MODE 1 
        elif state == STATE_MODE1:
            if ev1 == 'long':
                full_power_off()

            elif ev1 == 'double':
                motor.duty_u16(0)
                enter_standby()

            # sensor loop at fixed interval
            elif time.ticks_diff(now, last_dist_ms) >= config.DIST_INTERVAL_MS:
                last_dist_ms = now
                d = distance_cm(trig, echo)

                if d is None:
                    motor.duty_u16(0)
                    dbg("dist: None | duty: 0")
                else:
                    duty = duty_from_distance(d, config.NEAR, config.FAR)
                    dbg("dist: {} | duty: {}".format(d, duty))
                    motor.duty_u16(duty)

        # STATE: MODE 2 
        elif state == STATE_MODE2:
            if ev1 == 'long':
                full_power_off()

            elif ev2 == 'long':
                exit_mode2()

        time.sleep_ms(config.LOOP_SLEEP_MS)


if __name__ == "__main__":
    main()