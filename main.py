import os
import random
import time
import asyncio
import curses
import curses_tools
from  itertools import cycle

import physics
from explosion import explode
from obstacles import Obstacle, show_obstacles

TIC_TIMEOUT = 0.1 # 0.1 seconds
YEAR = 1957
OBSTACLES = []
OBSTACLES_COLLISIONS = []
SPEEDS = [0, 0] # start speed [row, column]
#
COROUTINES = []
#
GARBAGE_FRAMES = []
SPACESHIP_FRAMES = []
GAME_OVER_FRAME = ''


async def sleep(tics=1):
    """Sleep for 'tics' tics. 1 tics = TIC_TIMEOUT seconds"""
    for _ in range(tics):
        await asyncio.sleep(0)


async def game_over(canvas):
    rows, columns = curses_tools.get_frame_size(GAME_OVER_FRAME)
    max_row, max_column = canvas.getmaxyx()
    while True:
        curses_tools.draw_frame(canvas, (max_row - rows) / 2, (max_column - columns) / 2, GAME_OVER_FRAME)
        await sleep()


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await sleep()

    canvas.addstr(round(row), round(column), 'O')
    await sleep()
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        for obstacle in OBSTACLES:
            if obstacle.has_collision(row, column):
                OBSTACLES_COLLISIONS.append(obstacle)
                canvas.addstr(round(row), round(column), ' ')
                return
        await sleep()
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


async def animate_spaceship(canvas, row, column, max_row, max_column):
    rows, columns = curses_tools.get_frame_size(SPACESHIP_FRAMES[1])
    max_row, max_column = canvas.getmaxyx()
    next_row = row
    next_column = column
    previous_frame_index = 0
    x_speed, y_speed = SPEEDS
    while True:
        rows_direction, columns_direction, space_pressed = curses_tools.read_controls(canvas)
        if space_pressed and YEAR >= 2020:
            COROUTINES.append(
                fire(canvas, row, column + 2)
            )
        x_speed, y_speed = physics.update_speed(x_speed, y_speed, rows_direction, columns_direction)
        next_row = min(max(1, next_row + x_speed), max_row - rows - 1)
        next_column = min(max(1, next_column + y_speed), max_column - columns - 1)
        for index in range(len(SPACESHIP_FRAMES)):
            curses_tools.draw_frame(canvas, row, column, SPACESHIP_FRAMES[previous_frame_index], negative=True)
            for obstacle in OBSTACLES:
                if obstacle.has_collision(
                        int(row), int(column), obj_size_rows=rows, obj_size_columns=columns):
                    COROUTINES.append(explode(canvas, row + int(rows / 2), column + int(columns / 2)))
                    await game_over(canvas)
                    return
            next_frame_index = (previous_frame_index + index) % 2
            curses_tools.draw_frame(canvas, next_row, next_column, SPACESHIP_FRAMES[next_frame_index], negative=False)
            previous_frame_index = next_frame_index
            row = next_row
            column = next_column
            await sleep()


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()
    frame_rows, frame_columns = curses_tools.get_frame_size(garbage_frame)
    column = min(max(column, 0), columns_number - frame_columns - 1)
    row = 1
    obstacle = Obstacle(row, column, 1, frame_columns)
    OBSTACLES.append(obstacle)
    while row <= frame_rows:
        if obstacle in OBSTACLES_COLLISIONS:
            break
        tmp_frame = "\n".join(garbage_frame.split("\n")[-int(row):])
        curses_tools.draw_frame(canvas, 1, column, tmp_frame)
        obstacle.rows_size = int(row)
        await sleep()
        curses_tools.draw_frame(canvas, 1, column, tmp_frame, negative=True)
        row += speed
    row = 1
    while row < rows_number:
        if obstacle in OBSTACLES_COLLISIONS:
            COROUTINES.append(explode(canvas, row + int(frame_rows/2), column + int(frame_columns/2)))
            OBSTACLES_COLLISIONS.remove(obstacle)
            break
        curses_tools.draw_frame(canvas, row, column, garbage_frame)
        obstacle.row = int(row)
        await sleep()
        curses_tools.draw_frame(canvas, row, column, garbage_frame, negative=True)
        #
        if row + frame_rows + 1 >= rows_number:
            garbage_frame = "\n".join(garbage_frame.split("\n")[:-1])
        row += speed

    OBSTACLES.remove(obstacle)


async def show_year(canvas):
    phrase = ""
    global YEAR
    PHRASES = {
        1957: "First Sputnik",
        1961: "Gagarin flew!",
        1969: "Armstrong got on the moon!",
        1971: "First orbital space station Salute-1",
        1981: "Flight of the Shuttle Columbia",
        1998: 'ISS start building',
        2011: 'Messenger launch to Mercury',
        2020: "Take the plasma gun! Shoot the garbage!",
    }
    max_row, max_column = canvas.getmaxyx()
    while True:
        canvas.addstr(1, 2, "Currunt year: {}".format(YEAR))
        if YEAR in PHRASES:
            phrase = PHRASES[YEAR]
        canvas.addstr(2, 2, phrase)
        YEAR += 1
        await sleep(15)


async def blink(canvas, row, column, symbol='*', delay=0.1):
    """Draw the specified symbol in a blink"""
    while True:
        await sleep(round(delay/TIC_TIMEOUT))
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)
        canvas.addstr(row, column, symbol)
        await sleep(3)
        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)
        canvas.addstr(row, column, symbol)
        await sleep(5)


async def fill_orbit_with_garbage(canvas):
    rows_number, columns_number = canvas.getmaxyx()
    while True:
        if YEAR < 1961:
            await sleep()
        else:
            frame = random.choice(GARBAGE_FRAMES)
            rows, columns = curses_tools.get_frame_size(frame)
            COROUTINES.append(
                fly_garbage(canvas, random.randint(1, columns_number - columns - 2), frame)
            )
            await sleep(get_garbage_delay_tics(YEAR))


def get_garbage_delay_tics(year):
    if year < 1961:
        return None
    elif year < 1969:
        return 20
    elif year < 1981:
        return 14
    elif year < 1995:
        return 10
    elif year < 2010:
        return 8
    elif year < 2020:
        return 6
    else:
        return 2


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
        fill_orbit_with_garbage(canvas),
        show_year(canvas)
    ])
    # star animation
    COROUTINES.extend([blink(canvas=canvas,
                             row=random.randint(0, max_row - 1),
                             column=random.randint(0, max_col - 1),
                             delay=random.random()*3) for _ in range(100)])
    # COROUTINES.append(show_obstacles(canvas, OBSTACLES))
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

    with open(os.path.join('sprites', 'gameover.txt')) as file:
        GAME_OVER_FRAME = file.read()

    curses.update_lines_cols()
    curses.wrapper(draw)
