# This program was created in Arduino Lab for MicroPython

print('Hello, MicroPython!')
from arduino import *
from arduino_alvik import ArduinoAlvik

alvik = ArduinoAlvik()

SPEED = 30
DIST_THRESHOLD = 15
OPEN_THRESHOLD = 40

STATE_SEARCH_EXIT = 0
STATE_UP_RAMP = 1
STATE_WAIT = 2
STATE_DOWN_RAMP = 3
STATE_FINISHED = 4

state = STATE_SEARCH_EXIT
wait_start_time = 0

def setup():
    alvik.begin()
    delay(1000)

def loop():
    global state, wait_start_time

    left, cleft, center, cright, right = alvik.get_distance()
    ax, ay, az, pitch, roll, yaw = alvik.get_imu()  # Assuming this signature
    print(f"Pitch:{pitch:.1f}, DistC:{center}")

    # --- State Machine ---
    if state == STATE_SEARCH_EXIT:
        # Same logic as before to find exit
        if center > OPEN_THRESHOLD:
            alvik.set_wheels_speed(SPEED, SPEED)
        elif center < DIST_THRESHOLD or cleft < DIST_THRESHOLD or cright < DIST_THRESHOLD:
            if left > right:
                alvik.set_wheels_speed(-SPEED//2, SPEED//2)
            else:
                alvik.set_wheels_speed(SPEED//2, -SPEED//2)
        else:
            alvik.set_wheels_speed(SPEED, SPEED)

        # Detect ramp (pitch angle going > ~10 degrees upward)
        if pitch > 10:
            state = STATE_UP_RAMP

    elif state == STATE_UP_RAMP:
        alvik.set_wheels_speed(SPEED, SPEED)
        # When robot levels out (~0 degrees again), assume it's in middle of ramp
        if abs(pitch) < 5:
            alvik.stop()
            wait_start_time = millis()
            state = STATE_WAIT

    elif state == STATE_WAIT:
        if millis() - wait_start_time > 3000:  # Wait 3 seconds
            state = STATE_DOWN_RAMP

    elif state == STATE_DOWN_RAMP:
        alvik.set_wheels_speed(SPEED, SPEED)
        # Detect end of ramp when pitch stabilizes again near 0
        if abs(pitch) < 3 and center > OPEN_THRESHOLD:
            state = STATE_FINISHED

    elif state == STATE_FINISHED:
        alvik.stop()

def cleanup():
    alvik.stop()

start(setup, loop, cleanup)
