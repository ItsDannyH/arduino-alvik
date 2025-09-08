from arduino import *
from arduino_alvik import ArduinoAlvik
from collections import Counter

alvik = ArduinoAlvik()

SPEED = 25
COLOR_MARGIN = 15  # tolerance for detecting "new" color

# States
STATE_RECORD = 0
STATE_ANALYZE = 1
STATE_RETURN = 2
STATE_EXIT = 3

state = STATE_RECORD
colors_seen = []   # stores sequence of patches
unique_color = None
current_index = 0

def color_distance(c1, c2):
    # Euclidean distance between two RGB tuples
    return sum((a - b) ** 2 for a, b in zip(c1, c2)) ** 0.5

def setup():
    alvik.begin()
    delay(1000)

def loop():
    global state, colors_seen, unique_color, current_index

    # Example color read: returns (r,g,b)
    r, g, b = alvik.get_color()
    current_color = (r, g, b)

    if state == STATE_RECORD:
        alvik.set_wheels_speed(SPEED, SPEED)

        # Save patch if it's different from last one
        if not colors_seen or color_distance(colors_seen[-1], current_color) > COLOR_MARGIN:
            colors_seen.append(current_color)
            print(f"Recorded patch: {current_color}")

        # Condition: reached end of bridge → stop recording
        # Example: front sensor sees "no ground" or big gap
        _, _, center, _, _ = alvik.get_distance()
        if center > 80:  # exit detected
            alvik.stop()
            state = STATE_ANALYZE

    elif state == STATE_ANALYZE:
        # Count occurrences
        counter = Counter(tuple(c) for c in colors_seen)
        for c, count in counter.items():
            if count == 1:
                unique_color = c
                break
        print(f"Unique color found: {unique_color}")

        # Turn around to go back
        alvik.set_wheels_speed(-SPEED, -SPEED)
        delay(1000)
        alvik.stop()
        current_index = len(colors_seen) - 1
        state = STATE_RETURN

    elif state == STATE_RETURN:
        alvik.set_wheels_speed(SPEED, SPEED)

        # Watch patches in reverse
        if current_index >= 0:
            if color_distance(unique_color, current_color) <= COLOR_MARGIN:
                alvik.stop()
                print("Reached unique color patch → driving off")
                state = STATE_EXIT
            else:
                current_index -= 1

    elif state == STATE_EXIT:
        # Drive forward off the bridge
        alvik.set_wheels_speed(SPEED, SPEED)

def cleanup():
    alvik.stop()

start(setup, loop, cleanup)
