import time
from machine import Pin, PWM
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


def _check_uart(uart):
    # sends PING to Pi, waits up to 2 seconds for PONG response
    # this verifies the full round-trip: Pico TX → Pi RX → Pi TX → Pico RX
    try:
        # flush any stale data in the RX buffer
        while uart.any():
            uart.read()
 
        # send PING
        uart.write(b'PING\n')
        _log("  [    ] UART — sent PING, waiting for PONG...")
 
        # wait up to 2 seconds for response
        start = time.ticks_ms()
        response = b''
        while time.ticks_diff(time.ticks_ms(), start) < 2000:
            if uart.any():
                chunk = uart.read()
                if chunk:
                    response += chunk
                    # check if we got a complete PONG line
                    if b'PONG' in response:
                        _log("  [PASS] UART — handshake OK (Pi responded PONG)")
                        return True
            time.sleep_ms(10)
 
        _log("  [WARN] UART — no PONG received (Pi may not be running mode2.py)")
        return False
    except Exception as e:
        _log("  [FAIL] UART — {}".format(e))
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

 
def run_selfcheck(uart):
    # this runs all hardware checks in sequence
    # returns True if every check passed, False if any failed
    _log("\n========== SELF-CHECK START ==========")

    results = []
    results.append(_check_buzzer(config.BUZZER_PIN))
    results.append(_check_motor(config.MOTOR_PIN))
    results.append(_check_ultrasonic(config.TRIG_PIN, config.ECHO_PIN))
    results.append(_check_uart(uart))
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
