import os
from itertools import cycle

def get_frame_size(text):
    """Calculate size of multiline text fragment, return pair — number of rows and colums."""

    lines = text.splitlines()
    rows = len(lines)
    columns = max([len(line) for line in lines])
    return rows, columns


sprites = []

with open(os.path.join('sprites', 'rocket_frame_1.txt')) as file:
    sprites.append(file.read())

with open(os.path.join('sprites', 'rocket_frame_2.txt')) as file:
    sprites.append(file.read())


rows, columns = get_frame_size(sprites[0])
print(rows, columns)
rows, columns = get_frame_size(sprites[1])
print(rows, columns)

c = 0
for rocket in cycle(sprites):
    print(rocket)
    if c == 2:
        break
    c += 1

# class Star:
#     def __init__(self, row, column, symbol, style):
#         self.row = row
#         self.column = column
#         self.symbol = symbol
#         self.style = style
#
#     async def blink(self, canvas):
#         while True:
#             canvas.addstr(self.row, self.column, self.symbol, self.style)
#             await Sleep(2)
#
#             canvas.addstr(self.row, self.column, self.symbol)
#             await Sleep(0.3)
#
#             canvas.addstr(self.row, self.column, self.symbol, curses.A_BOLD)
#             await Sleep(0.5)
#
#             canvas.addstr(self.row, self.column, self.symbol)
#             await Sleep(0.3)