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
    def __init__(self, seconds):
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
    for spaceship in cycle(sprites_spaceship):
        canvas.nodelay(True)
        rows_direction, columns_direction, _ = read_controls(canvas)
        rows_offset += rows_direction
        columns_offset += columns_direction
        if (max_row // 2 + rows // 2 + rows_offset >= max_row-1) or (max_column // 2 + columns // 2 + columns_offset >= max_column-1) \
            or (max_row // 2 - rows // 2 + rows_offset <= 0) or (max_column // 2 - columns // 2 + columns_offset <= 0):
            rows_offset -= rows_direction
            columns_offset -= columns_direction
        draw_frame(canvas, max_row // 2 - rows // 2 + rows_offset, max_column // 2 - columns // 2 + columns_offset, spaceship, negative=False)
        await Sleep(0.1)
        draw_frame(canvas, max_row // 2 - rows // 2 + rows_offset, max_column // 2 - columns // 2 + columns_offset, spaceship, negative=True)


async def blink(canvas, row, column, symbol='*'):
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await Sleep(2)

        canvas.addstr(row, column, symbol)
        await Sleep(0.3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await Sleep(0.5)

        canvas.addstr(row, column, symbol)
        await Sleep(0.3)
        

async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await Sleep(0.1)

    canvas.addstr(round(row), round(column), 'O')
    await Sleep(0.1)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await Sleep(0.1)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def draw(canvas):
    row_max, col_max = canvas.getmaxyx()
    spaceship = animate_spaceship(canvas)
    coroutines = ([blink(canvas=canvas,
                         row=random.randint(1, row_max - 2),
                         column=random.randint(1, col_max - 2),
                         symbol=random.choice('+*.:')
                         ) for i in range(100)]
                  + [spaceship])
    
    sleeping_coroutines = [
        [random.random()*5, star] for star in coroutines
    ] + [[0, spaceship]]

    curses.curs_set(False)
    canvas.border()

    while sleeping_coroutines:
        min_timeout, _ = min(sleeping_coroutines, key=lambda x: x[0])
        sleeping_coroutines = [
            [timeout - min_timeout, star] for timeout, star in sleeping_coroutines
        ]
        time.sleep(min_timeout)

        active_coroutines = [coroutine for coroutine in sleeping_coroutines if coroutine[0] <= 0]
        sleeping_coroutines = [coroutines for coroutines in sleeping_coroutines if coroutines[0] > 0]

        for _, coroutine in active_coroutines.copy():
            try:
                sleep_command = coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                continue
            except RuntimeError:
                continue
            seconds_to_sleep = sleep_command.seconds
            sleeping_coroutines.append([seconds_to_sleep, coroutine])


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
