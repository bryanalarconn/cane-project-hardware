from machine import PWM
import time

# this module handles all buzzer feedback for power on/off events

def _beep(pin, freq_hz, duration_ms):
    # this drives  passive buzzer with a PWM signal at the given frequency
    bz = PWM(pin)
    bz.freq(freq_hz)
    bz.duty_u16(32768)
    time.sleep_ms(duration_ms)
    bz.duty_u16(0)
    bz.deinit()                 # release PWM so pin is free after  beep

def power_on_sound(pin):
    # this plays a rising two-tone chirp to signal device is on
    # low tone then high tone, ascending = starting up
    _beep(pin, 800,  120)       # low tone first
    time.sleep_ms(60)
    _beep(pin, 1600, 180)       # high tone second

def power_off_sound(pin):
    # this plays a falling two-tone chirp to signal device is off
    # high tone then low tone, descending = shutting down
    _beep(pin, 1600, 120)       # high tone first
    time.sleep_ms(60)
    _beep(pin, 600,  300)       # low tone last

def error_sound(pin):
    # this plays three rapid beeps to signal something went wrong
    for _ in range(3):
        _beep(pin, 440, 80)
        time.sleep_ms(80)