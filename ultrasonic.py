import time

# this module expects you to pass trig/echo Pins in
# it returns distance in cm (float) or None on timeout

def distance_cm(trig, echo, timeout_us=30000):
    # this starts the ultrasonic pulse
    trig.low()
    time.sleep_us(2)
    trig.high()
    time.sleep_us(10)
    trig.low()

    # this waits for the echo pin to go high (start of return pulse)
    start = time.ticks_us()
    while echo.value() == 0:
        if time.ticks_diff(time.ticks_us(), start) > timeout_us:
            return None  # timeout waiting for echo to start

    # this waits for the echo pin to go low (end of return pulse)
    t0 = time.ticks_us()
    while echo.value() == 1:
        if time.ticks_diff(time.ticks_us(), t0) > timeout_us:
            return None  # timeout waiting for echo to end

    # this then calculates the distance in cm
    # HC-SR04-style rule of thumb: microseconds / 58 ≈ cm
    return time.ticks_diff(time.ticks_us(), t0) / 58.0