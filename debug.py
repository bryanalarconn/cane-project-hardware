import config

# this module provides the debug print function used everywhere
# controlled by DEBUG flag in config.py
# set DEBUG = False in config.py to silence all output

def dbg(msg):
    if config.DEBUG:
        print("[DBG] {}".format(msg))
