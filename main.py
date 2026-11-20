#!/usr/bin/env python3
"""The World in One Page -- 20 November 2026.

A tiny newspaper front page drawn entirely with the Python standard
library. No network, no randomness, no wall-clock time: running this
script twice produces a byte-identical image.png next to itself.

Layout: a masthead dated 20 November 2026, then a 3 x 2 grid of story
panels. Each panel carries a kicker, a headline, a short body, one stat
line and a small geometric icon drawn with code.
"""

import binascii
import os
import struct
import zlib

# --------------------------------------------------------------------------
# Canvas
# --------------------------------------------------------------------------

WIDTH = 1600
HEIGHT = 1050

PAPER = (248, 243, 231)   # warm newsprint
CARD = (255, 253, 246)    # panel paper
INK = (26, 26, 26)        # headline ink
BODY_INK = (52, 52, 52)   # body ink
RED = (166, 25, 46)       # kicker / accent red
BLUE = (31, 76, 120)      # icon accent blue
GREY = (120, 116, 108)    # rules and small print
LIGHT_GREY = (210, 205, 192)


class Canvas:
    """A plain RGB pixel buffer with a few drawing primitives."""

    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(width * height * 3)
        r, g, b = colour
        for i in range(0, len(self.pixels), 3):
            self.pixels[i] = r
            self.pixels[i + 1] = g
            self.pixels[i + 2] = b

    def set_pixel(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i] = colour[0]
            self.pixels[i + 1] = colour[1]
            self.pixels[i + 2] = colour[2]

    def fill_rect(self, x, y, w, h, colour):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set_pixel(xx, yy, colour)

    def rect(self, x, y, w, h, colour, thickness=1):
        for t in range(thickness):
            for xx in range(x, x + w):
                self.set_pixel(xx, y + t, colour)
                self.set_pixel(xx, y + h - 1 - t, colour)
            for yy in range(y, y + h):
                self.set_pixel(x + t, yy, colour)
                self.set_pixel(x + w - 1 - t, yy, colour)

    def hline(self, x, y, length, colour, thickness=1):
        self.fill_rect(x, y, length, thickness, colour)

    def vline(self, x, y, length, colour, thickness=1):
        self.fill_rect(x, y, thickness, length, colour)

    def line(self, x0, y0, x1, y1, colour, thickness=1):
        """Bresenham line, with a square brush for thickness."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.fill_rect(x - thickness // 2, y - thickness // 2,
                           thickness, thickness, colour)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, colour, thickness=1, filled=False):
        for yy in range(cy - r - 1, cy + r + 2):
            for xx in range(cx - r - 1, cx + r + 2):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if filled:
                    if d2 <= r * r:
                        self.set_pixel(xx, yy, colour)
                else:
                    if abs(d2 - r * r) <= r * thickness:
                        self.set_pixel(xx, yy, colour)

    def triangle(self, x0, y0, x1, y1, x2, y2, colour, filled=False):
        if filled:
            min_y = min(y0, y1, y2)
            max_y = max(y0, y1, y2)
            for yy in range(min_y, max_y + 1):
                xs = []
                for (ax, ay, bx, by) in ((x0, y0, x1, y1),
                                         (x1, y1, x2, y2),
                                         (x2, y2, x0, y0)):
                    if ay == by:
                        continue
                    if min(ay, by) <= yy <= max(ay, by):
                        t = (yy - ay) / (by - ay)
                        xs.append(ax + t * (bx - ax))
                if len(xs) >= 2:
                    for xx in range(int(min(xs)), int(max(xs)) + 1):
                        self.set_pixel(xx, yy, colour)
        else:
            self.line(x0, y0, x1, y1, colour, 2)
            self.line(x1, y1, x2, y2, colour, 2)
            self.line(x2, y2, x0, y0, colour, 2)


# --------------------------------------------------------------------------
# 5x7 bitmap font (rows are 5-bit numbers, high bit = leftmost pixel)
# --------------------------------------------------------------------------

FONT = {
    ' ': (0, 0, 0, 0, 0, 0, 0),
    '!': (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000, 0b00100),
    '"': (0b01010, 0b01010, 0b01010, 0b00000, 0b00000, 0b00000, 0b00000),
    '#': (0b01010, 0b01010, 0b11111, 0b01010, 0b11111, 0b01010, 0b01010),
    '$': (0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100),
    '%': (0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011),
    '&': (0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    "'": (0b00100, 0b00100, 0b01000, 0b00000, 0b00000, 0b00000, 0b00000),
    '(': (0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010),
    ')': (0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000),
    '*': (0b00000, 0b10101, 0b01110, 0b11111, 0b01110, 0b10101, 0b00000),
    '+': (0b00000, 0b00100, 0b00100, 0b11111, 0b00100, 0b00100, 0b00000),
    ',': (0b00000, 0b00000, 0b00000, 0b00000, 0b00100, 0b00100, 0b01000),
    '-': (0b00000, 0b00000, 0b00000, 0b11111, 0b00000, 0b00000, 0b00000),
    '.': (0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00110, 0b00110),
    '/': (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    '0': (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    '1': (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    '2': (0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111),
    '3': (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    '4': (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    '5': (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    '6': (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    '7': (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    '8': (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    '9': (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    ':': (0b00000, 0b00100, 0b00000, 0b00000, 0b00000, 0b00100, 0b00000),
    ';': (0b00000, 0b00100, 0b00000, 0b00000, 0b00100, 0b00100, 0b01000),
    '<': (0b00010, 0b00100, 0b01000, 0b10000, 0b01000, 0b00100, 0b00010),
    '=': (0b00000, 0b00000, 0b11111, 0b00000, 0b11111, 0b00000, 0b00000),
    '>': (0b01000, 0b00100, 0b00010, 0b00001, 0b00010, 0b00100, 0b01000),
    '?': (0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b00000, 0b00100),
    '@': (0b01110, 0b10001, 0b10111, 0b10101, 0b10110, 0b10000, 0b01110),
    'A': (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'B': (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    'C': (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    'D': (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    'E': (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    'F': (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    'G': (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    'H': (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'I': (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    'J': (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    'K': (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    'L': (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    'M': (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    'N': (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    'O': (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'P': (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    'Q': (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    'R': (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    'S': (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    'T': (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    'U': (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'V': (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    'W': (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001),
    'X': (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    'Y': (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    'Z': (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    '[': (0b01110, 0b01000, 0b01000, 0b01000, 0b01000, 0b01000, 0b01110),
    '\\': (0b10000, 0b01000, 0b01000, 0b00100, 0b00010, 0b00010, 0b00001),
    ']': (0b01110, 0b00010, 0b00010, 0b00010, 0b00010, 0b00010, 0b01110),
    '^': (0b00100, 0b01010, 0b10001, 0b00000, 0b00000, 0b00000, 0b00000),
    '_': (0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b11111),
    '`': (0b00100, 0b00100, 0b00010, 0b00000, 0b00000, 0b00000, 0b00000),
    'a': (0b00000, 0b00000, 0b01110, 0b00001, 0b01111, 0b10001, 0b01111),
    'b': (0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b10001, 0b11110),
    'c': (0b00000, 0b00000, 0b01110, 0b10000, 0b10000, 0b10001, 0b01110),
    'd': (0b00001, 0b00001, 0b01111, 0b10001, 0b10001, 0b10001, 0b01111),
    'e': (0b00000, 0b00000, 0b01110, 0b10001, 0b11111, 0b10000, 0b01110),
    'f': (0b00110, 0b01001, 0b01000, 0b11110, 0b01000, 0b01000, 0b01000),
    'g': (0b00000, 0b01111, 0b10001, 0b10001, 0b01111, 0b00001, 0b01110),
    'h': (0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b10001, 0b10001),
    'i': (0b00100, 0b00000, 0b01100, 0b00100, 0b00100, 0b00100, 0b01110),
    'j': (0b00010, 0b00000, 0b00110, 0b00010, 0b00010, 0b10010, 0b01100),
    'k': (0b10000, 0b10000, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010),
    'l': (0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    'm': (0b00000, 0b00000, 0b11010, 0b10101, 0b10101, 0b10101, 0b10101),
    'n': (0b00000, 0b00000, 0b11110, 0b10001, 0b10001, 0b10001, 0b10001),
    'o': (0b00000, 0b00000, 0b01110, 0b10001, 0b10001, 0b10001, 0b01110),
    'p': (0b00000, 0b00000, 0b11110, 0b10001, 0b11110, 0b10000, 0b10000),
    'q': (0b00000, 0b00000, 0b01111, 0b10001, 0b01111, 0b00001, 0b00001),
    'r': (0b00000, 0b00000, 0b10110, 0b11001, 0b10000, 0b10000, 0b10000),
    's': (0b00000, 0b00000, 0b01111, 0b10000, 0b01110, 0b00001, 0b11110),
    't': (0b01000, 0b01000, 0b11100, 0b01000, 0b01000, 0b01001, 0b00110),
    'u': (0b00000, 0b00000, 0b10001, 0b10001, 0b10001, 0b10011, 0b01101),
    'v': (0b00000, 0b00000, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    'w': (0b00000, 0b00000, 0b10001, 0b10101, 0b10101, 0b11011, 0b10001),
    'x': (0b00000, 0b00000, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001),
    'y': (0b00000, 0b00000, 0b10001, 0b10001, 0b01111, 0b00001, 0b01110),
    'z': (0b00000, 0b00000, 0b11111, 0b00010, 0b00100, 0b01000, 0b11111),
    '{': (0b00010, 0b00100, 0b00100, 0b01100, 0b00100, 0b00100, 0b00010),
    '|': (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    '}': (0b01000, 0b00100, 0b00100, 0b00110, 0b00100, 0b00100, 0b01000),
    '~': (0b00000, 0b00000, 0b01001, 0b10110, 0b00000, 0b00000, 0b00000),
}


def text_width(text, scale):
    """Pixel width of a string at the given scale."""
    return len(text) * 6 * scale - scale


def draw_text(canvas, x, y, text, scale, colour):
    """Draw text with the top-left corner at (x, y)."""
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT['?'])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits & (1 << (4 - col)):
                    canvas.fill_rect(cx + col * scale, y + row * scale,
                                     scale, scale, colour)
        cx += 6 * scale
    return cx


def draw_text_centred(canvas, cx, y, text, scale, colour):
    draw_text(canvas, cx - text_width(text, scale) // 2, y, text, scale,
              colour)


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    char_w = 6 * scale
    max_chars = max(1, max_width // char_w)
    lines = []
    for paragraph in text.split('\n'):
        words = paragraph.split(' ')
        current = ''
        for word in words:
            trial = word if not current else current + ' ' + word
            if len(trial) <= max_chars:
                current = trial
            else:
                if current:
                    lines.append(current)
                # A single over-long word is hard-split.
                while len(word) > max_chars:
                    lines.append(word[:max_chars])
                    word = word[max_chars:]
                current = word
        if current:
            lines.append(current)
    return lines


# --------------------------------------------------------------------------
# PNG encoder (stdlib only)
# --------------------------------------------------------------------------

def _chunk(kind, data):
    out = struct.pack('>I', len(data)) + kind + data
    out += struct.pack('>I', binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(path, canvas):
    raw = bytearray()
    row_len = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)  # filter: none
        start = y * row_len
        raw += canvas.pixels[start:start + row_len]
    data = b'\x89PNG\r\n\x1a\n'
    data += _chunk(b'IHDR', struct.pack('>IIBBBBB', canvas.width,
                                        canvas.height, 8, 2, 0, 0, 0))
    data += _chunk(b'IDAT', zlib.compress(bytes(raw), 9))
    data += _chunk(b'IEND', b'')
    with open(path, 'wb') as fh:
        fh.write(data)


# --------------------------------------------------------------------------
# The news of 20 November 2026 (researched on the morning of the day)
# --------------------------------------------------------------------------

STORIES = [
    {
        'kicker': 'SUMMIT IN BEIJING',
        'headline': 'Trump, Xi and Putin sign joint peace declaration',
        'body': ('The three leaders held an unprecedented trilateral '
                 'summit in China and issued a joint declaration on '
                 'peace, covering nuclear risks, energy security and '
                 'the wars in Ukraine and the Middle East.'),
        'stat': '1st ever three-way summit',
        'icon': 'summit',
    },
    {
        'kicker': 'WASHINGTON',
        'headline': 'Trump puts Iran decision off until 2027',
        'body': ('President Trump said there is no rush to decide on '
                 'military action against Iran, telling reporters he '
                 'will see what happens after January 1 and pushing '
                 'any decision into next year.'),
        'stat': 'Decision pushed past 1 Jan 2027',
        'icon': 'clock',
    },
    {
        'kicker': 'THE HAGUE',
        'headline': 'UN court: Myanmar committed genocide',
        'body': ('The International Court of Justice ruled that '
                 "Myanmar's military committed genocide against the "
                 'Rohingya minority in its 2017 crackdown, a landmark '
                 'judgment for international law.'),
        'stat': 'Ruling follows the 2017 crackdown',
        'icon': 'scales',
    },
    {
        'kicker': 'DEEP SPACE',
        'headline': 'Voyager 1 reaches a light-day from Earth',
        'body': ('NASA confirmed the 1977 probe is now so far away '
                 'that a radio signal takes a full day to reach it, '
                 'a first for any human-made object.'),
        'stat': '1 light-day away - launched 1977',
        'icon': 'probe',
    },
    {
        'kicker': 'ODISHA, INDIA',
        'headline': 'Cyclone Akvan drives 300,000 to shelters',
        'body': ('Authorities evacuated hundreds of thousands of '
                 'people and deployed more than 400 rescue teams as '
                 'the severe storm bore down on the east coast, with '
                 'landfall expected today.'),
        'stat': '300,000 evacuated - 423 rescue teams',
        'icon': 'cyclone',
    },
    {
        'kicker': 'WALL STREET',
        'headline': 'Anthropic IPO is the biggest ever',
        'body': ('The maker of the Claude chatbot raised $81 billion '
                 'in its market debut, valuing the company at about '
                 '$1.5 trillion, even as US stocks fell on doubts '
                 'about the AI boom.'),
        'stat': '$81bn raised - ~$1.5tn valuation',
        'icon': 'chart',
    },
]


# --------------------------------------------------------------------------
# Icons: small geometric drawings, one per story
# --------------------------------------------------------------------------

def draw_icon(canvas, kind, x, y, size, colour, accent):
    """Draw a geometric icon inside the square (x, y, size, size)."""
    cx = x + size // 2
    cy = y + size // 2
    if kind == 'summit':
        # Three overlapping circles: three leaders, one table.
        for dx, dy, r in ((-26, -14, 17), (26, -14, 17), (0, 18, 17)):
            canvas.circle(cx + dx, cy + dy, r, colour, 3)
        canvas.hline(x + 8, cy + 40, size - 16, colour, 3)
    elif kind == 'clock':
        # A clock face with hands pointing at the new year.
        canvas.circle(cx, cy, 34, colour, 3)
        canvas.circle(cx, cy, 4, accent, filled=True)
        canvas.line(cx, cy, cx, cy - 24, colour, 3)
        canvas.line(cx, cy, cx + 18, cy + 8, colour, 3)
        canvas.circle(cx, cy, 40, accent, 2)
    elif kind == 'scales':
        # Scales of justice.
        canvas.vline(cx, y + 8, size - 24, colour, 3)
        canvas.hline(x + 12, y + 16, size - 24, colour, 3)
        canvas.circle(cx, y + 8, 5, accent, filled=True)
        for sx in (x + 12, x + size - 12):
            canvas.line(sx, y + 16, sx, y + 44, colour, 2)
            canvas.triangle(sx - 18, y + 44, sx + 18, y + 44, sx, y + 62,
                            colour, filled=True)
        canvas.hline(x + 8, cy + 40, size - 16, colour, 3)
    elif kind == 'probe':
        # A probe on a dotted path toward a distant star.
        for i in range(6):
            px = x + 6 + i * 9
            canvas.circle(px, y + size - 10 - i * 7, 2, GREY, filled=True)
        canvas.triangle(cx + 6, y + 8, cx - 14, y + 44, cx + 26, y + 44,
                        colour, filled=True)
        canvas.line(cx - 6, y + 46, cx - 12, y + 62, accent, 3)
        canvas.line(cx + 6, y + 46, cx + 12, y + 62, accent, 3)
        canvas.line(cx + 18, y + 46, cx + 24, y + 62, accent, 3)
        canvas.circle(cx + 34, y + 16, 6, accent, filled=True)
    elif kind == 'cyclone':
        # A spiral of concentric arcs.
        for r in (34, 26, 18, 10):
            canvas.circle(cx, cy, r, colour if r % 16 else accent, 3)
        canvas.circle(cx, cy, 3, accent, filled=True)
    elif kind == 'chart':
        # Rising bars with an arrow.
        bars = (16, 28, 22, 40, 52)
        bw = 14
        base = y + size - 12
        for i, h in enumerate(bars):
            bx = x + 8 + i * 20
            canvas.fill_rect(bx, base - h, bw, h,
                             accent if i == len(bars) - 1 else colour)
        tip_x = x + size - 10
        tip_y = base - 62
        canvas.line(x + 6, base - 18, tip_x, tip_y, accent, 3)
        canvas.line(tip_x, tip_y, tip_x - 16, tip_y + 2, accent, 3)
        canvas.line(tip_x, tip_y, tip_x - 2, tip_y + 16, accent, 3)


# --------------------------------------------------------------------------
# Page layout
# --------------------------------------------------------------------------

MARGIN = 40
GRID_TOP = 208
GRID_BOTTOM = 890
STRIP_TOP = 904
FOOTER_Y = 1002

# Short one-line briefs for the strip at the foot of the page.
BRIEFS = [
    'GTA 6 - Sales pass $1.8bn, overtaking The Odyssey global run',
    'UKRAINE - European leaders say they are ready for talks with Russia',
    'SPACE - Engine trouble ends Hayabusa2 asteroid landing plan',
]


def draw_masthead(canvas):
    # Double rule frame around the whole page.
    canvas.rect(24, 24, WIDTH - 48, HEIGHT - 48, INK, 2)
    canvas.rect(30, 30, WIDTH - 60, HEIGHT - 60, GREY, 1)

    title = 'THE WORLD IN ONE PAGE'
    draw_text_centred(canvas, WIDTH // 2, 56, title, 9, INK)
    canvas.hline(MARGIN, 142, WIDTH - 2 * MARGIN, INK, 2)
    dateline = ('FRIDAY, 20 NOVEMBER 2026   |   SIX STORIES FROM AROUND '
                'THE WORLD   |   ONE PAGE')
    draw_text_centred(canvas, WIDTH // 2, 156, dateline, 2, BODY_INK)
    canvas.hline(MARGIN, 184, WIDTH - 2 * MARGIN, INK, 3)


def draw_panel(canvas, story, x, y, w, h):
    canvas.fill_rect(x, y, w, h, CARD)
    canvas.rect(x, y, w, h, INK, 2)
    pad = 18
    inner_x = x + pad
    inner_w = w - 2 * pad
    icon_size = 96
    icon_x = x + w - pad - icon_size
    icon_y = y + pad

    # Icon in the top-right corner, framed by a light rule.
    canvas.rect(icon_x - 6, icon_y - 6, icon_size + 12, icon_size + 12,
               LIGHT_GREY, 1)
    draw_icon(canvas, story['icon'], icon_x, icon_y, icon_size, INK, RED)

    # Kicker and headline share the left column beside the icon.
    text_w = inner_w - icon_size - 14
    draw_text(canvas, inner_x, y + pad + 4, story['kicker'], 2, RED)
    headline_lines = wrap_text(story['headline'], text_w, 3)
    hy = y + pad + 30
    for line in headline_lines:
        draw_text(canvas, inner_x, hy, line, 3, INK)
        hy += 24

    # Body spans the full panel width below the icon block.
    body_y = y + pad + icon_size + 18
    body_lines = wrap_text(story['body'], inner_w, 2)
    by = body_y
    for line in body_lines:
        draw_text(canvas, inner_x, by, line, 2, BODY_INK)
        by += 21

    # Stat line pinned to the bottom of the panel.
    stat_y = y + h - 40
    canvas.hline(inner_x, stat_y - 12, inner_w, LIGHT_GREY, 1)
    draw_text(canvas, inner_x, stat_y, story['stat'], 2, BLUE)


def draw_briefs(canvas):
    """A strip of three short items under the main grid."""
    canvas.hline(MARGIN, STRIP_TOP, WIDTH - 2 * MARGIN, INK, 2)
    draw_text(canvas, MARGIN, STRIP_TOP + 10, 'ALSO IN THE NEWS', 2, RED)
    by = STRIP_TOP + 32
    for brief in BRIEFS:
        draw_text(canvas, MARGIN + 18, by, brief, 2, BODY_INK)
        by += 17


def draw_footer(canvas):
    canvas.hline(MARGIN, FOOTER_Y - 12, WIDTH - 2 * MARGIN, INK, 2)
    note = ('Compiled from wire reports on the morning of 20 November '
            '2026 - all figures as reported')
    draw_text_centred(canvas, WIDTH // 2, FOOTER_Y + 4, note, 2, GREY)


def build():
    canvas = Canvas(WIDTH, HEIGHT, PAPER)
    draw_masthead(canvas)

    cols = 3
    rows = 2
    gap_x = 24
    gap_y = 16
    grid_w = WIDTH - 2 * MARGIN
    panel_w = (grid_w - (cols - 1) * gap_x) // cols
    panel_h = (GRID_BOTTOM - GRID_TOP - (rows - 1) * gap_y) // rows

    for i, story in enumerate(STORIES):
        col = i % cols
        row = i // cols
        px = MARGIN + col * (panel_w + gap_x)
        py = GRID_TOP + row * (panel_h + gap_y)
        draw_panel(canvas, story, px, py, panel_w, panel_h)

    draw_briefs(canvas)
    draw_footer(canvas)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'image.png')
    write_png(out, canvas)
    print('wrote', out, WIDTH, 'x', HEIGHT)


if __name__ == '__main__':
    build()
