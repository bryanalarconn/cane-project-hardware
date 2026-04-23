import time
from machine import Pin, PWM, UART
import config
from drivers.buzzer import error_sound
from drivers.ultrasonic import distance_cm

# this module runs once at boot to test each peripheral

# returns True if everything passed, False otherwise
# main.py continues either way

def _log(msg):
    if config.DEBUG:
        print(msg)


def _check_buzzer(buz_pin):
    # this drives the buzzer at 1kHz for 80ms to confirm PWM works
    try:
        pin = Pin(buz_pin, Pin.OUT)
        bz = PWM(pin)
        bz.freq(1000)
        bz.duty_u16(32768)      # 50% duty = loudest for passive buzzer
        time.sleep_ms(80)
        bz.duty_u16(0)
        bz.deinit()             # release PWM so pin is free for later
        _log("  [PASS] Buzzer (GP{})".format(buz_pin))
        return True
    except Exception as e:
        _log("  [FAIL] Buzzer (GP{}) — {}".format(buz_pin, e))
        return False


def _check_motor(motor_pin):
    # this spins the vibration motor briefly at low intensity
    try:
        pin = Pin(motor_pin, Pin.OUT)
        m = PWM(pin)
        m.freq(200)
        m.duty_u16(20000)
        time.sleep_ms(200)
        m.duty_u16(0)
        m.deinit()
        _log("  [PASS] Motor (GP{})".format(motor_pin))
        return True
    except Exception as e:
        _log("  [FAIL] Motor (GP{}) — {}".format(motor_pin, e))
        return False


def _check_ultrasonic(trig_pin, echo_pin):
    # this fires one ultrasonic reading
    # None means the echo never came back
    # issue or just nothing within range (sensor times out at ~5m)
    # we report WARN instead of FAIL because a timeout at boot
    # is normal if there's no object nearby
    try:
        trig = Pin(trig_pin, Pin.OUT)
        echo = Pin(echo_pin, Pin.IN)
        d = distance_cm(trig, echo)
        if d is not None:
            _log("  [PASS] Ultrasonic — {:.1f} cm".format(d))
            return True
        else:
            _log("  [WARN] Ultrasonic — no echo (sensor may not be connected)")
            return False
    except Exception as e:
        _log("  [FAIL] Ultrasonic — {}".format(e))
        return False


def _check_uart():
    # this initialises UART0 and sends a test string to the Pi
    # we can't verify the Pi received it
    # but if the UART constructor itself fails we catch it
    try:
        uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))
        uart.write(b'SELFCHECK_PING\n')
        _log("  [PASS] UART0 TX (GP0 → Pi)")
        return True
    except Exception as e:
        _log("  [FAIL] UART0 — {}".format(e))
        return False


def _check_button(pin_num, label):
    # this verifies a button pin reads HIGH when not pressed
    # both buttons use internal PULL_UP so idle = 1
    # if it reads 0 the button might be stuck or someone is holding it
    try:
        p = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        val = p.value()
        if val == 1:
            _log("  [PASS] {} (GP{}) — idle HIGH".format(label, pin_num))
            return True
        else:
            _log("  [WARN] {} (GP{}) — reads LOW (stuck or held?)".format(
                label, pin_num))
            return False
    except Exception as e:
        _log("  [FAIL] {} (GP{}) — {}".format(label, pin_num, e))
        return False


def run_selfcheck():
    # this runs all hardware checks in sequence
    # returns True if every check passed, False if any failed
    _log("\n========== SELF-CHECK START ==========")

    # run each check and collect True/False results
    results = []
    results.append(_check_buzzer(config.BUZZER_PIN))
    results.append(_check_motor(config.MOTOR_PIN))
    results.append(_check_ultrasonic(config.TRIG_PIN, config.ECHO_PIN))
    results.append(_check_uart())
    results.append(_check_button(config.BTN_PIN,  "SW1 (main)"))
    results.append(_check_button(config.YOLO_PIN, "SW2 (YOLO)"))

    # tally results
    passed = sum(results)
    total  = len(results)
    all_ok = (passed == total)

    if all_ok:
        _log("All checks PASSED.")
    else:
        _log("Some checks FAILED — review output")
    _log("========== SELF-CHECK END ============\n")

    # audible feedback so you know the result without reading console
    # all OK = short 2kHz chirp,  failures = three rapid error beeps
    buz = Pin(config.BUZZER_PIN, Pin.OUT)
    if all_ok:
        bz = PWM(buz)
        bz.freq(2000)
        bz.duty_u16(32768)
        time.sleep_ms(100)
        bz.duty_u16(0)
        bz.deinit()
    else:
        error_sound(buz)

    return all_ok