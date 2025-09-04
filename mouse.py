from arduino import *
from arduino_alvik import ArduinoAlvik

alvik = ArduinoAlvik()

# -----------------------
# Calibration constants (tweak these)
# -----------------------
CELL_MS = 800        # ms to move forward one maze cell (adjust)
TURN_MS = 780        # ms for ~90° turn (adjust)
TURN_BACK_MS = 1500  # ms for ~180° turn (adjust)
SPEED = 100          # wheel speed magnitude
DIST_THRESHOLD_CM = 15  # distance threshold to consider "wall" (cm)

# -----------------------
# Movement helpers (use set_wheels_speed like your track code)
# -----------------------
def stop(short_delay_ms=100):
    alvik.set_wheels_speed(0, 0)
    delay(short_delay_ms)

def move_forward(duration_ms=CELL_MS, speed=SPEED):
    alvik.set_wheels_speed(speed, speed)
    delay(duration_ms)
    stop()

def turn_left(duration_ms=TURN_MS, speed=SPEED):
    # left rotation: left wheel negative, right wheel positive
    alvik.set_wheels_speed(-speed, speed)
    delay(duration_ms)
    stop()

def turn_right(duration_ms=TURN_MS, speed=SPEED):
    alvik.set_wheels_speed(speed, -speed)
    delay(duration_ms)
    stop()

def turn_back(duration_ms=TURN_BACK_MS, speed=SPEED):
    alvik.set_wheels_speed(speed, -speed)
    delay(duration_ms)
    stop()

# -----------------------
# Sensor wrappers
# -----------------------
# Try a few likely Alvik API names inside try/except, otherwise fallback.
def _read_distance_front():
    # try common method names; modify if your library differs
    try:
        return alvik.read_distance_front()
    except Exception:
        try:
            return alvik.read_distance()  # generic
        except Exception:
            try:
                return alvik.ultrasonic_front()
            except Exception:
                return None

def _read_distance_left():
    try:
        return alvik.read_distance_left()
    except Exception:
        try:
            return alvik.ultrasonic_left()
        except Exception:
            return None

def _read_distance_right():
    try:
        return alvik.read_distance_right()
    except Exception:
        try:
            return alvik.ultrasonic_right()
        except Exception:
            return None

def front_is_clear():
    d = _read_distance_front()
    if d is None:
        # fallback: unknown sensor -> assume clear (change to False to be conservative)
        print("Warning: front distance not available — assuming CLEAR. Replace sensor code!")
        return True
    return d > DIST_THRESHOLD_CM

def left_is_clear():
    d = _read_distance_left()
    if d is None:
        print("Warning: left distance not available — assuming CLEAR. Replace sensor code!")
        return True
    return d > DIST_THRESHOLD_CM

def right_is_clear():
    d = _read_distance_right()
    if d is None:
        print("Warning: right distance not available — assuming CLEAR. Replace sensor code!")
        return True
    return d > DIST_THRESHOLD_CM

# -----------------------
# Maze/navigation state
# -----------------------
# heading: 0=N, 1=E, 2=S, 3=W
heading = 0
pos = (0, 0)             # start cell
visited = set()          # visited cells (x,y)
junction_stack = []      # stack of junctions: {"pos":(x,y), "heading":h, "options":[...]} 

def _pos_forward(x, y, h):
    if h == 0:   # North -> y+1
        return (x, y + 1)
    elif h == 1: # East -> x+1
        return (x + 1, y)
    elif h == 2: # South -> y-1
        return (x, y - 1)
    elif h == 3: # West -> x-1
        return (x - 1, y)

def update_position_after_move(move):
    """
    Update global pos and heading after a logical move:
      - 'F' : forward
      - 'L' : turn left then forward
      - 'R' : turn right then forward
      - 'B' : turn back then forward
    """
    global pos, heading
    x, y = pos

    if move == "F":
        pos = _pos_forward(x, y, heading)
    elif move == "L":
        heading = (heading - 1) % 4
        pos = _pos_forward(x, y, heading)
    elif move == "R":
        heading = (heading + 1) % 4
        pos = _pos_forward(x, y, heading)
    elif move == "B":
        heading = (heading + 2) % 4
        pos = _pos_forward(x, y, heading)

    visited.add(pos)

# -----------------------
# Exploration step (one iteration)
# -----------------------
def explore_step():
    global pos, heading, junction_stack

    # Sense options relative to current heading
    options = []
    if left_is_clear():   options.append("L")
    if front_is_clear():  options.append("F")
    if right_is_clear():  options.append("R")

    # If more than one option (a junction, i.e., a choice point), push it on stack.
    # We store a copy of options (unexplored moves)
    if len(options) > 1:
        junction_stack.append({
            "pos": pos,
            "heading": heading,
            "options": options.copy()
        })
        print("Pushed junction:", pos, "heading:", heading, "options:", options)

    # Choose next move, favoring Left > Forward > Right
    next_move = None
    if "L" in options: next_move = "L"
    elif "F" in options: next_move = "F"
    elif "R" in options: next_move = "R"

    # If there is a junction stored at current pos, remove chosen option from its list
    if next_move and junction_stack:
        top = junction_stack[-1]
        if top["pos"] == pos:
            if next_move in top["options"]:
                top["options"].remove(next_move)
                print("Chose", next_move, "from junction at", pos, "remaining:", top["options"])

    if next_move:
        # execute the movement
        if next_move == "L":
            turn_left()
        elif next_move == "R":
            turn_right()
        elif next_move == "F":
            # no rotation, just go forward
            pass

        move_forward(CELL_MS)
        update_position_after_move(next_move)

        print("Moved", next_move, "-> now at", pos, "heading", heading)

    else:
        # dead end or no clear direction: backtrack
        print("Dead end at", pos, " — backtracking one cell")
        # If there are no junctions left, exploration is complete
        if not junction_stack:
            print("Junction stack empty -> exploration complete.")
            # stop motors and do nothing (or optionally search for entrance)
            stop()
            # We leave loop() running; user can power-cycle or extend behavior
            return

        # If top of stack refers to current pos and still has options, we should try them (but options empty since next_move None)
        # If top of stack refers to current pos and has no options -> pop and move back
        # If top of stack refers to another pos -> move back one cell (toward previous cell)
        # We'll move back one cell by turning 180 and driving forward
        # Before moving back, if the top junction is at the current pos but has no options, pop it:
        while junction_stack and junction_stack[-1]["pos"] == pos and not junction_stack[-1]["options"]:
            popped = junction_stack.pop()
            print("Popped exhausted junction:", popped["pos"])

        # now perform a single back step (180 turn + forward)
        turn_back()
        move_forward(CELL_MS)
        update_position_after_move("B")
        print("Backtracked one cell -> now at", pos, "heading", heading)

# -----------------------
# Setup / Loop / Cleanup
# -----------------------
def setup():
    alvik.begin()
    delay(1000)
    print("Alvik started, beginning exploration.")

def loop():
    explore_step()
    delay(100)

def cleanup():
    alvik.stop()
    print("Cleanup: stopped Alvik.")

# Kick off the event loop
start(setup, loop, cleanup)
