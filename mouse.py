import time

# ------------------
# Robot control stubs (replace with Alvik motor + sensor code)
# ------------------
def move_forward():
    print("Forward")
    time.sleep(0.5)

def turn_left():
    print("Turn Left")
    time.sleep(0.5)

def turn_right():
    print("Turn Right")
    time.sleep(0.5)

def turn_back():
    print("Turn Around")
    time.sleep(1.0)

def front_is_clear(): return True
def left_is_clear():  return True
def right_is_clear(): return True

# ------------------
# Maze state
# ------------------
# Heading encoded as 0=N, 1=E, 2=S, 3=W
heading = 0
pos = (0, 0)

# Stack of junctions
junction_stack = []

def update_position(move):
    global pos, heading
    x, y = pos
    if move == "F":
        if heading == 0: y += 1
        elif heading == 1: x += 1
        elif heading == 2: y -= 1
        elif heading == 3: x -= 1
    elif move == "L":
        heading = (heading - 1) % 4
        # then step forward
        update_position("F")
        return
    elif move == "R":
        heading = (heading + 1) % 4
        update_position("F")
        return
    elif move == "B":
        heading = (heading + 2) % 4
        update_position("F")
        return
    pos = (x, y)

# ------------------
# Main exploration logic
# ------------------
def explore():
    global pos, heading

    while True:
        # sense available paths
        options = []
        if left_is_clear():   options.append("L")
        if front_is_clear():  options.append("F")
        if right_is_clear():  options.append("R")

        if len(options) > 1:
            # junction → push to stack
            junction_stack.append({
                "pos": pos,
                "heading": heading,
                "options": options
            })

        # pick next move (favor L > F > R)
        next_move = None
        if "L" in options: next_move = "L"
        elif "F" in options: next_move = "F"
        elif "R" in options: next_move = "R"

        if next_move:
            # perform move
            if next_move == "L": turn_left()
            elif next_move == "R": turn_right()
            elif next_move == "F": pass
            move_forward()
            update_position(next_move)

            # remove chosen option from last junction
            if junction_stack and junction_stack[-1]["pos"] == pos:
                if next_move in junction_stack[-1]["options"]:
                    junction_stack[-1]["options"].remove(next_move)
        else:
            # dead end → backtrack
            if not junction_stack:
                print("Exploration complete.")
                break
            junction = junction_stack[-1]
            if not junction["options"]:
                junction_stack.pop()
                turn_back()
                move_forward()
                update_position("B")
            else:
                # unexplored option still exists → try it next loop
                pass

        print("At:", pos, "Heading:", heading, "Stack:", junction_stack)
        time.sleep(0.1)

# ------------------
# Start
# ------------------
explore()
