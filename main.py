import os
import random
import time
import asyncio
import curses
from  itertools import cycle

TIC_TIMEOUT = 0.1 # 0.1 seconds
# SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258

#
COROUTINES = []
#
GARBAGE_FRAMES = []
SPACESHIP_FRAMES = []

def read_controls(canvas):
    """Read keys pressed and returns tuple witl controls state."""

    rows_direction = columns_direction = 0
    space_pressed = False

    while True:
        pressed_key_code = canvas.getch()

        if pressed_key_code == -1:
            # https://docs.python.org/3/library/curses.html#curses.window.getch
            break

        if pressed_key_code == UP_KEY_CODE:
            rows_direction = -1

        if pressed_key_code == DOWN_KEY_CODE:
            rows_direction = 1

        if pressed_key_code == RIGHT_KEY_CODE:
            columns_direction = 1

        if pressed_key_code == LEFT_KEY_CODE:
            columns_direction = -1

        # if pressed_key_code == SPACE_KEY_CODE:
        #     space_pressed = True

    return rows_direction, columns_direction, space_pressed


def draw_frame(canvas, start_row, start_column, text, negative=False):
    """Draw multiline text fragment on canvas, erase text instead of drawing if negative=True is specified."""

    rows_number, columns_number = canvas.getmaxyx()

    for row, line in enumerate(text.splitlines(), round(start_row)):
        if row < 0:
            continue

        if row >= rows_number:
            break

        for column, symbol in enumerate(line, round(start_column)):
            if column < 0:
                continue

            if column >= columns_number:
                break

            if symbol == ' ':
                continue

            # Check that current position it is not in a lower right corner of the window
            # Curses will raise exception in that case. Don`t ask why…
            # https://docs.python.org/3/library/curses.html#curses.window.addch
            if row == rows_number - 1 and column == columns_number - 1:
                continue

            symbol = symbol if not negative else ' '
            canvas.addch(row, column, symbol)


def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""
    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


async def animate_spaceship(canvas, row, column, max_row, max_column):
    rows, columns = get_frame_size(SPACESHIP_FRAMES[1])
    max_row, max_column = canvas.getmaxyx()
    next_row = row
    next_column = column
    previous_frame_index = 0
    while True:
        rows_direction, columns_direction, _ = read_controls(canvas)
        if rows_direction ** 2 or columns_direction ** 2:
            next_row = min(max(1, row + rows_direction), max_row - rows - 1)
            next_column = min(max(1, column + columns_direction), max_column - columns - 1)
        for index in range(len(SPACESHIP_FRAMES)):
            draw_frame(canvas, row, column, SPACESHIP_FRAMES[previous_frame_index], negative=True)
            next_frame_index = (previous_frame_index + index) % 2
            draw_frame(canvas, next_row, next_column, SPACESHIP_FRAMES[next_frame_index], negative=False)
            previous_frame_index = next_frame_index
            row = next_row
            column = next_column
            await asyncio.sleep(0)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    column = max(column, 0)
    column = min(column, columns_number - 1)
    row = 0
    while row < rows_number:
        draw_frame(canvas, row, column, garbage_frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed


async def blink(canvas, row, column, symbol='*', delay=0.1):
    """Draw the specified symbol in a blink"""
    while True:
        for _ in range(round(delay/TIC_TIMEOUT)):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


async def fill_orbit_with_garbage(canvas, p=0.15):
    rows_number, columns_number = canvas.getmaxyx()
    while True:
        if random.random() > (1 - p):
            frame = random.choice(GARBAGE_FRAMES)
            frame_rows, frame_columns = get_frame_size(frame)
            COROUTINES.append(
                fly_garbage(canvas, random.randint(1, columns_number - frame_columns - 2), frame)
            )
        await asyncio.sleep(0)


def draw(canvas):
    max_row, max_col = canvas.getmaxyx()
    canvas.border()
    canvas.timeout(int(TIC_TIMEOUT * 1000))
    canvas.nodelay(True)
    curses.curs_set(False)
    COROUTINES.extend([
        animate_spaceship(canvas,
                          row=max_row // 2,
                          column=max_col // 2,
                          max_row=max_row,
                          max_column=max_col),
        fill_orbit_with_garbage(canvas)
    ])
    # star animation
    COROUTINES.extend([blink(canvas=canvas,
                             row=random.randint(0, max_row - 1),
                             column=random.randint(0, max_col - 1),
                             delay=random.random()*3) for _ in range(100)])
    while True:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)

        canvas.refresh()
        time.sleep(TIC_TIMEOUT)


if __name__ == '__main__':
    for file in os.listdir("sprites/garbage"):
        if file.endswith(".txt"):
            with open(os.path.join("sprites/garbage", file)) as file:
                GARBAGE_FRAMES.append(file.read())
    with open(os.path.join('sprites', 'rocket_frame_1.txt')) as file:
        SPACESHIP_FRAMES.append(file.read())

    with open(os.path.join('sprites', 'rocket_frame_2.txt')) as file:
        SPACESHIP_FRAMES.append(file.read())
    curses.update_lines_cols()
    curses.wrapper(draw)
