from machine import PWM, Pin

# this module wraps PWM motor behavior + distance->duty mapping

def duty_from_distance(d, NEAR, FAR):
    # this function maps distance to motor duty cycle by reacting to the distance, either near or far
    # - NEAR or closer  => full power
    # - FAR or farther  => off
    # - between         => linear ramp
    if d <= NEAR:
        return 65535
    if d >= FAR:
        return 0
    return int(65535 * (FAR - d) / (FAR - NEAR))

def setup_motor(pin, freq=200):
    # force pin LOW first to kill any floating signal on boot / re-init
    quiet = Pin(pin.id() if hasattr(pin, 'id') else pin, Pin.OUT, value=0)

    # vibration motor: PWM lets us "scale" vibration intensity smoothly
    m = PWM(quiet)
    m.freq(freq)     # ~200Hz is a decent vib motor PWM frequency
    m.duty_u16(0)    # start off / no vibration
    return m