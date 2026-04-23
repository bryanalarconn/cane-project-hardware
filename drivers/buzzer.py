from machine import PWM
import config
import time

# this module handles all buzzer feedback for power on/off events
# sound definitions live in config.py

def _beep(pin, freq_hz, duration_ms):
    # this drives  passive buzzer with a PWM signal at the given frequency
    bz = PWM(pin)
    bz.freq(freq_hz)
    bz.duty_u16(32768)
    time.sleep_ms(duration_ms)
    bz.duty_u16(0)
    bz.deinit()                 # release PWM so pin is free after  beep

def play_sound(pin, sound):
    # this walks through a tuple of (freq, duration) steps from config.py
    # a step with freq == 0 is treated as a silent gap between tones
    for freq, dur in sound:
        if freq == 0:
            time.sleep_ms(dur)
        else:
            _beep(pin, freq, dur)


def power_on_sound(pin):
    # this plays a rising two-tone chirp to signal device is on
    # low tone then high tone, ascending = starting up
    play_sound(pin, config.SOUND_POWER_ON)
 
def power_off_sound(pin):
    # this plays a falling two-tone chirp to signal device is off
    # high tone then low tone, descending = shutting down
    play_sound(pin, config.SOUND_POWER_OFF)
 
def mode_start_sound(pin):
    # this plays a quick ascending chirp when entering a mode
    # lets the user know the mode is now active
    play_sound(pin, config.SOUND_MODE_START)
 
def mode_stop_sound(pin):
    # this plays a quick descending chirp when leaving a mode
    # lets the user know the mode has ended
    play_sound(pin, config.SOUND_MODE_STOP)
 
def error_sound(pin):
    # this plays three rapid beeps to signal something went wrong
    play_sound(pin, config.SOUND_ERROR)