import os
import random
import time
import asyncio
import curses
from  itertools import cycle

# SPACE_KEY_CODE = 32
LEFT_KEY_CODE = 260
RIGHT_KEY_CODE = 261
UP_KEY_CODE = 259
DOWN_KEY_CODE = 258


class EventLoopCommand:
    def __await__(self):
        return (yield self)


class Sleep(EventLoopCommand):
    def __init__(self, seconds=0.1):
        self.seconds = seconds


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


async def animate_spaceship(canvas):
    sprites_spaceship = []
    with open(os.path.join('sprites', 'rocket_frame_1.txt')) as file:
        sprites_spaceship.append(file.read())
        sprites_spaceship.append(file.read())
    with open(os.path.join('sprites', 'rocket_frame_2.txt')) as file:
        sprites_spaceship.append(file.read())
        sprites_spaceship.append(file.read())

    rows, columns = get_frame_size(sprites_spaceship[0])
    max_row, max_column = canvas.getmaxyx()
    rows_offset = 0
    columns_offset = 0
    canvas.nodelay(True)
    for spaceship in cycle(sprites_spaceship):
        rows_direction, columns_direction, _ = read_controls(canvas)
        rows_offset += rows_direction
        columns_offset += columns_direction
        if (max_row // 2 + rows // 2 + rows_offset >= max_row-1) or (max_column // 2 + columns // 2 + columns_offset >= max_column-1) \
            or (max_row // 2 - rows // 2 + rows_offset <= 0) or (max_column // 2 - columns // 2 + columns_offset <= 0):
            rows_offset -= rows_direction
            columns_offset -= columns_direction
        draw_frame(canvas, max_row // 2 - rows // 2 + rows_offset, max_column // 2 - columns // 2 + columns_offset,
                   spaceship, negative=False)
        await Sleep()
        draw_frame(canvas, max_row // 2 - rows // 2 + rows_offset, max_column // 2 - columns // 2 + columns_offset, spaceship, negative=True)


async def blink(canvas, row, column, symbol='*', delay=0.1):
    while True:
        for _ in range(round(delay/0.1)):
            await Sleep()
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await Sleep()
        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await Sleep()
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await Sleep()
        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await Sleep()


def draw(canvas):
    row_max, col_max = canvas.getmaxyx()
    spaceship = animate_spaceship(canvas)
    coroutines = ([blink(canvas=canvas,
                         row=random.randint(1, row_max - 2),
                         column=random.randint(1, col_max - 2),
                         symbol=random.choice('+*.:'),
                         delay=random.random() * 3
                         ) for i in range(100)]
                  + [spaceship])

    curses.curs_set(False)
    canvas.border()
    while coroutines:
        for coroutine in coroutines:
            try:
                coroutine.send(None)

            except StopIteration:
                coroutines.remove(coroutine)
            except RuntimeError:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(0.1)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
