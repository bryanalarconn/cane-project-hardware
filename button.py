import time

# this button class provides:
# - debounce
# - single click
# - double click
# - long press
#
# note: button is active-low (pressed == 0)

class Button:
    def __init__(self, pin, DEBOUNCE_MS=50, DOUBLE_CLICK_MS=400, LONG_PRESS_MS=3000):
        self._pin = pin
        self._DEBOUNCE_MS = DEBOUNCE_MS
        self._DOUBLE_CLICK_MS = DOUBLE_CLICK_MS
        self._LONG_PRESS_MS = LONG_PRESS_MS

        self._last_val    = pin.value()
        self._last_change = time.ticks_ms()
        self._press_start = None
        self._long_done   = False
        self._pending     = False
        self._pend_time   = 0

    def tick(self):
        now = time.ticks_ms()
        val = self._pin.value()
        event = None

        # debounce edge detection
        # edge = True means we detected a *press* transition after debounce
        edge = False
        if val != self._last_val and time.ticks_diff(now, self._last_change) > self._DEBOUNCE_MS:
            self._last_change = now
            self._last_val = val
            edge = (val == 0)

        # this detects button press/release events and whether they are single/double clicks
        if edge:
            # on a press, start timing for long-press
            if self._press_start is None:  # first press detected
                self._press_start = now
                self._long_done = False

            # if we already had a click pending, this press could be the second click
            if self._pending and time.ticks_diff(now, self._pend_time) <= self._DOUBLE_CLICK_MS:  # double click detected
                self._pending = False
                event = 'double'
            else:
                # otherwise we start (or restart) the pending single click window
                self._pending   = True
                self._pend_time = now

        # this detects long-press while held
        # only fire once per hold (guarded by _long_done)
        if not event and val == 0 and self._press_start is not None and not self._long_done:  # long press candidate
            if time.ticks_diff(now, self._press_start) >= self._LONG_PRESS_MS:  # long press duration met
                self._long_done = True
                self._pending   = False
                event = 'long'

        # if button released, reset hold tracking (click tracking is handled separately)
        if val == 1 and self._press_start is not None:
            self._press_start = None
            self._long_done   = False

        # pending single-click timeout
        # if no second click appears within DOUBLE_CLICK_MS, it becomes a single click
        if not event and self._pending and time.ticks_diff(now, self._pend_time) > self._DOUBLE_CLICK_MS:
            self._pending = False
            event = 'single'

        return event