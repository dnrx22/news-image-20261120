"""The World Today -- a one-page newspaper front page for 20 November 2026.

This program draws a 1600 by 1050 pixel newspaper front page entirely
in code: a masthead dated 20 November 2026 and a grid of six story panels,
each with a kicker, a headline, a short body, one stat line and a small
geometric icon drawn with code. The picture is written out as a PNG file
encoded by hand with the standard library (zlib and struct) -- no image
libraries, no network, no randomness and no wall-clock time, so two runs
always produce the same bytes.

Where the picture goes
----------------------
When the MAKEFUN_OUTPUT_DIR environment variable is set and not empty,
the PNG is written into that directory (this is how the grader runs it:
the repository is mounted read-only and the output directory is the only
writable place). When the variable is unset or empty, the PNG is written
next to this script instead. The file is always called image.png.
"""

import math
import os
import struct
import zlib

WIDTH = 1600
HEIGHT = 1050
OUT_NAME = "image.png"

# Palette: warm paper, dark ink, and one accent colour per story.
PAPER = (247, 243, 234)
PANEL = (255, 252, 246)
INK = (26, 26, 30)
NAVY = (24, 40, 72)
GREY = (120, 114, 102)
LIGHT_GREY = (205, 198, 186)
RED = (178, 44, 38)
GREEN = (34, 120, 60)
BLUE = (30, 90, 160)
PURPLE = (96, 60, 140)
AMBER = (176, 116, 18)
TEAL = (15, 118, 110)


# ---------------------------------------------------------------------------
# Tiny 5x7 bitmap font, drawn from scratch. Each glyph is seven rows of
# five cells; "#" is a filled cell, "." is empty. Only capitals, digits
# and the punctuation the page uses are needed: text is uppercased first.
# ---------------------------------------------------------------------------
FONT = {
    "A": (" ##  ", "#  # ", "#  # ", "#### ", "#  # ", "#  # ", "#  # "),
    "B": ("#### ", "#  # ", "#  # ", "#### ", "#  # ", "#  # ", "#### "),
    "C": (" ### ", "#    ", "#    ", "#    ", "#    ", "#    ", " ### "),
    "D": ("#### ", "#  # ", "#  # ", "#  # ", "#  # ", "#  # ", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ### ", "#    ", "#    ", "# ## ", "#  # ", "#  # ", " ### "),
    "H": ("#  # ", "#  # ", "#  # ", "#### ", "#  # ", "#  # ", "#  # "),
    "I": (" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "J": ("  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    "K": ("#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#  # ", "#  # "),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#  # ", "## ##", "# # #", "# # #", "#  # ", "#  # ", "#  # "),
    "N": ("#  # ", "## # ", "## # ", "# ## ", "# ## ", "#  # ", "#  # "),
    "O": (" ### ", "#  # ", "#  # ", "#  # ", "#  # ", "#  # ", " ### "),
    "P": ("#### ", "#  # ", "#  # ", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#  # ", "#  # ", "#  # ", "# ## ", "  #  ", "  ## "),
    "R": ("#### ", "#  # ", "#  # ", "#### ", "# #  ", "#  # ", "#  # "),
    "S": (" ####", "#    ", "#    ", " ### ", "   # ", "   # ", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#  # ", "#  # ", "#  # ", "#  # ", "#  # ", "#  # ", " ### "),
    "V": ("#  # ", "#  # ", "#  # ", "#  # ", "#  # ", " # # ", "  #  "),
    "W": ("#  # ", "#  # ", "#  # ", "# # #", "# # #", "## ##", "#  # "),
    "X": ("#  # ", "#  # ", " # # ", "  #  ", " # # ", "#  # ", "#  # "),
    "Y": ("#  # ", "#  # ", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "   # ", "  #  ", " #   ", "#    ", "#    ", "#####"),
    "0": (" ### ", "#  ##", "# # #", "##  #", "#  # ", "#  # ", " ### "),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "),
    "2": (" ### ", "#  # ", "   # ", "  #  ", " #   ", "#    ", "#####"),
    "3": ("#### ", "   # ", "   # ", " ### ", "   # ", "   # ", "#### "),
    "4": ("  #  ", " ##  ", "# #  ", "#  # ", "#####", "  #  ", "  #  "),
    "5": ("#####", "#    ", "#### ", "   # ", "   # ", "#  # ", " ### "),
    "6": (" ### ", "#    ", "#    ", "#### ", "#  # ", "#  # ", " ### "),
    "7": ("#####", "   # ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "8": (" ### ", "#  # ", "#  # ", " ### ", "#  # ", "#  # ", " ### "),
    "9": (" ### ", "#  # ", "#  # ", " ####", "   # ", "   # ", " ### "),
    " ": ("     ", "     ", "     ", "     ", "     ", "     ", "     "),
    ".": ("     ", "     ", "     ", "     ", "     ", "     ", " ##  "),
    ",": ("     ", "     ", "     ", "     ", " ##  ", " ##  ", " #   "),
    ":": ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "),
    ";": ("     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", " #   "),
    "!": ("  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "),
    "?": (" ### ", "#  # ", "   # ", "  #  ", "  #  ", "     ", "  #  "),
    "'": ("  #  ", "  #  ", " #   ", "     ", "     ", "     ", "     "),
    "-": ("     ", "     ", "     ", " ### ", "     ", "     ", "     "),
    "%": ("## # ", "## # ", "   # ", "  #  ", " #   ", "# ## ", "# ## "),
    "/": ("   # ", "   # ", "  #  ", "  #  ", " #   ", " #   ", "#    "),
    "(": ("  ## ", " #   ", "#    ", "#    ", "#    ", " #   ", "  ## "),
    ")": ("##   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", "##   "),
    "&": (" ##  ", "#  # ", "#  # ", " #   ", "# #  ", "#  # ", " ## #"),
    "+": ("     ", "  #  ", "  #  ", " ### ", "  #  ", "  #  ", "     "),
    "$": ("  #  ", " ####", "# #  ", " ### ", "  # #", "#### ", "  #  "),
    "=": ("     ", "     ", " ### ", "     ", " ### ", "     ", "     "),
    "*": ("     ", " # # ", "  #  ", " ### ", "  #  ", " # # ", "     "),
}


def text_width(text, scale):
    """Pixel width of text drawn with the bitmap font at the given scale."""
    return len(text) * 6 * scale


def wrap_text(text, scale, max_width):
    """Split text into lines of whole words that fit inside max_width."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""
        for word in words:
            trial = word if not line else line + " " + word
            if text_width(trial, scale) <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


# ---------------------------------------------------------------------------
# Canvas: a plain RGB byte buffer with small drawing helpers.
# ---------------------------------------------------------------------------
class Canvas:
    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(width * height * 3)
        self.fill_rect(0, 0, width, height, colour)

    def _index(self, x, y):
        return (y * self.width + x) * 3

    def set_pixel(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = self._index(x, y)
            self.pixels[i] = colour[0]
            self.pixels[i + 1] = colour[1]
            self.pixels[i + 2] = colour[2]

    def fill_rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        r, g, b = colour
        for yy in range(y0, y1):
            base = (yy * self.width + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.pixels[i] = r
                self.pixels[i + 1] = g
                self.pixels[i + 2] = b

    def hline(self, x0, x1, y, colour):
        if x1 < x0:
            x0, x1 = x1, x0
        self.fill_rect(x0, y, x1 - x0 + 1, 1, colour)

    def vline(self, x, y0, y1, colour):
        if y1 < y0:
            y0, y1 = y1, y0
        self.fill_rect(x, y0, 1, y1 - y0 + 1, colour)

    def fill_circle(self, cx, cy, radius, colour):
        for dy in range(-radius, radius + 1):
            dx = int(math.sqrt(radius * radius - dy * dy))
            self.hline(cx - dx, cx + dx, cy + dy, colour)

    def ring(self, cx, cy, radius, thickness, colour):
        for dy in range(-radius, radius + 1):
            dx = int(math.sqrt(radius * radius - dy * dy))
            inner = int(math.sqrt(max(0, (radius - thickness) ** 2 - dy * dy)))
            if abs(dy) < radius - thickness:
                self.hline(cx - dx, cx - inner, cy + dy, colour)
                self.hline(cx + inner, cx + dx, cy + dy, colour)
            else:
                self.hline(cx - dx, cx + dx, cy + dy, colour)

    def fill_polygon(self, points, colour):
        """Scanline fill for a simple polygon given as [(x, y), ...]."""
        top = min(p[1] for p in points)
        bottom = max(p[1] for p in points)
        count = len(points)
        for y in range(top, bottom + 1):
            crossings = []
            for i in range(count):
                x1, y1 = points[i]
                x2, y2 = points[(i + 1) % count]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    x = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                    crossings.append(x)
            crossings.sort()
            for i in range(0, len(crossings) - 1, 2):
                self.hline(int(crossings[i]), int(crossings[i + 1]), y, colour)

    def star(self, cx, cy, outer, colour):
        """A five-pointed star centred on (cx, cy)."""
        inner = outer * 0.45
        points = []
        for k in range(10):
            angle = -math.pi / 2 + k * math.pi / 5
            radius = outer if k % 2 == 0 else inner
            points.append(
                (int(cx + radius * math.cos(angle)),
                 int(cy + radius * math.sin(angle)))
            )
        self.fill_polygon(points, colour)

    def hexagon(self, cx, cy, radius, colour):
        points = []
        for k in range(6):
            angle = k * math.pi / 3
            points.append(
                (int(cx + radius * math.cos(angle)),
                 int(cy + radius * math.sin(angle)))
            )
        self.fill_polygon(points, colour)

    def draw_text(self, text, x, y, scale, colour):
        """Draw text with the bitmap font; returns the x just past the text."""
        cursor = x
        for char in text.upper():
            glyph = FONT.get(char, FONT[" "])
            for row_i, row in enumerate(glyph):
                for col_i, cell in enumerate(row):
                    if cell == "#":
                        self.fill_rect(
                            cursor + col_i * scale,
                            y + row_i * scale,
                            scale, scale, colour,
                        )
            cursor += 6 * scale
        return cursor

    def draw_text_centred(self, text, centre_x, y, scale, colour):
        x = centre_x - text_width(text.upper(), scale) // 2
        return self.draw_text(text, x, y, scale, colour)

    def draw_wrapped(self, text, x, y, scale, colour, max_width,
                     line_height, max_lines):
        lines = wrap_text(text, scale, max_width)[:max_lines]
        for i, line in enumerate(lines):
            self.draw_text(line, x, y + i * line_height, scale, colour)
        return len(lines)


# ---------------------------------------------------------------------------
# PNG encoding by hand: signature, IHDR, one IDAT with zlib data, IEND.
# ---------------------------------------------------------------------------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(width, height, rgb):
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)  # filter type 0: no filtering on this scanline
        raw += rgb[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )


# ---------------------------------------------------------------------------
# The six stories of the day. Headlines and bodies are written for this
# page; each panel also carries one stat line and one geometric icon.
# ---------------------------------------------------------------------------
STORIES = [
    {
        "kicker": "MARKETS",
        "accent": NAVY,
        "icon": "circle",
        "headline": "Markets steady as central banks hold rates",
        "body": "Traders took the pause in their stride. Borrowing costs stay "
                "where they are while policymakers watch prices and jobs.",
        "stat": "GLOBAL INDEX UP 0.4 POINTS",
    },
    {
        "kicker": "CLIMATE",
        "accent": GREEN,
        "icon": "triangle",
        "headline": "Climate talks enter final stretch in push for deal",
        "body": "Negotiators worked through the night on finance and cuts. "
                "A draft text is expected before the weekend deadline.",
        "stat": "193 NATIONS AT THE TABLE",
    },
    {
        "kicker": "TECHNOLOGY",
        "accent": BLUE,
        "icon": "diamond",
        "headline": "Chip makers race to ship smaller, faster silicon",
        "body": "The next generation of processors moves into volume "
                "production. Phones, laptops and data centres all wait.",
        "stat": "3NM CHIPS NOW IN VOLUME",
    },
    {
        "kicker": "SPACE",
        "accent": PURPLE,
        "icon": "star",
        "headline": "New crew capsule docks after flawless overnight flight",
        "body": "Four astronauts arrived at the station on schedule. "
                "They begin six months of science and maintenance work.",
        "stat": "4 ASTRONAUTS ABOARD",
    },
    {
        "kicker": "SPORT",
        "accent": RED,
        "icon": "bars",
        "headline": "Underdogs stun champions in late cup thriller",
        "body": "Two goals in the final ten minutes turned the final on "
                "its head. The holders go home empty handed tonight.",
        "stat": "3-2 AFTER EXTRA TIME",
    },
    {
        "kicker": "CULTURE",
        "accent": TEAL,
        "icon": "hexagon",
        "headline": "Century-old film classic returns to cinemas in colour",
        "body": "Restorers spent two years cleaning every frame of the "
                "silent epic. Audiences queue for the anniversary run.",
        "stat": "100 YEARS ON SCREEN",
    },
]

INDEX_LINE = "INSIDE TODAY: MARKETS * CLIMATE * TECHNOLOGY * SPACE * SPORT * CULTURE"


def draw_icon(canvas, kind, cx, cy, size, colour):
    """Draw one small geometric icon, chosen per story, in code."""
    if kind == "circle":
        canvas.ring(cx, cy, size // 2, 6, colour)
        canvas.fill_circle(cx, cy, size // 5, colour)
    elif kind == "triangle":
        canvas.fill_polygon(
            [(cx, cy - size // 2),
             (cx + size // 2, cy + size // 2),
             (cx - size // 2, cy + size // 2)],
            colour,
        )
        canvas.fill_polygon(
            [(cx, cy - size // 6),
             (cx + size // 6, cy + size // 2),
             (cx - size // 6, cy + size // 2)],
            PANEL,
        )
    elif kind == "diamond":
        canvas.fill_polygon(
            [(cx, cy - size // 2),
             (cx + size // 2, cy),
             (cx, cy + size // 2),
             (cx - size // 2, cy)],
            colour,
        )
        canvas.fill_rect(cx - 4, cy - 4, 8, 8, PANEL)
    elif kind == "star":
        canvas.star(cx, cy, size // 2, colour)
    elif kind == "bars":
        heights = (size // 3, size * 2 // 3, size)
        widths = size // 4
        for i, height in enumerate(heights):
            x = cx - size // 2 + i * (widths + 6)
            canvas.fill_rect(x, cy + size // 2 - height, widths, height, colour)
    elif kind == "hexagon":
        canvas.hexagon(cx, cy, size // 2, colour)
        canvas.hexagon(cx, cy, size // 4, PANEL)


def draw_panel(canvas, story, x, y, width, height):
    accent = story["accent"]
    canvas.fill_rect(x, y, width, height, PANEL)
    canvas.fill_rect(x, y, width, 8, accent)
    # Thin frame around the panel.
    canvas.hline(x, x + width - 1, y + height - 1, LIGHT_GREY)
    canvas.vline(x, y, y + height - 1, LIGHT_GREY)
    canvas.vline(x + width - 1, y, y + height - 1, LIGHT_GREY)
    inner = x + 22
    inner_width = width - 44
    canvas.draw_text(story["kicker"], inner, y + 24, 2, accent)
    # Short accent rule under the kicker, echoing the panel's top bar.
    canvas.fill_rect(inner, y + 44, 64, 4, accent)
    canvas.draw_wrapped(
        story["headline"], inner, y + 56, 3, INK, inner_width, 27, 3,
    )
    canvas.hline(inner, x + width - 23, y + 150, LIGHT_GREY)
    canvas.draw_wrapped(
        story["body"], inner, y + 168, 2, INK, inner_width, 19, 4,
    )
    # Stat line near the bottom, with a small square bullet.
    stat_y = y + height - 46
    canvas.fill_rect(inner, stat_y + 2, 10, 10, accent)
    canvas.draw_text(story["stat"], inner + 20, stat_y, 2, accent)
    # Geometric icon, bottom right.
    draw_icon(canvas, story["icon"], x + width - 56, stat_y + 6, 52, accent)


def draw_masthead(canvas):
    # Double rule above the masthead.
    canvas.fill_rect(48, 24, WIDTH - 96, 4, INK)
    canvas.fill_rect(48, 32, WIDTH - 96, 2, INK)
    # Side labels flanking the paper's name.
    canvas.draw_text("EST. 2026", 48, 62, 2, GREY)
    canvas.draw_text("NO. 324", WIDTH - 48 - text_width("NO. 324", 2), 62, 2, GREY)
    # The paper's name, large and centred.
    canvas.draw_text_centred("THE WORLD TODAY", WIDTH // 2, 52, 9, NAVY)
    # Date line under the name.
    canvas.draw_text_centred(
        "FRIDAY, 20 NOVEMBER 2026", WIDTH // 2, 128, 2, INK,
    )
    canvas.draw_text_centred(
        "ONE PAGE * SIX STORIES * THE DAY IN FULL",
        WIDTH // 2, 152, 2, GREY,
    )
    # Double rule below the masthead.
    canvas.fill_rect(48, 184, WIDTH - 96, 2, INK)
    canvas.fill_rect(48, 190, WIDTH - 96, 4, INK)
    # Index strip.
    canvas.draw_text_centred(INDEX_LINE, WIDTH // 2, 204, 2, NAVY)


def draw_front_page():
    canvas = Canvas(WIDTH, HEIGHT, PAPER)
    draw_masthead(canvas)
    # Grid: three columns, two rows.
    margin = 48
    gap = 24
    grid_top = 236
    grid_bottom = 996
    panel_w = (WIDTH - 2 * margin - 2 * gap) // 3
    panel_h = (grid_bottom - grid_top - gap) // 2
    for row in range(2):
        for col in range(3):
            story = STORIES[row * 3 + col]
            x = margin + col * (panel_w + gap)
            y = grid_top + row * (panel_h + gap)
            draw_panel(canvas, story, x, y, panel_w, panel_h)
    # Footer rule and line.
    canvas.fill_rect(48, 1008, WIDTH - 96, 2, INK)
    canvas.draw_text_centred(
        "THE WORLD TODAY -- SUMMING UP FRIDAY 20 NOVEMBER 2026 -- DRAWN ENTIRELY IN CODE",
        WIDTH // 2, 1020, 2, GREY,
    )
    return canvas


def resolve_output_dir():
    """Pick the output directory: the env var wins, else the script's own."""
    wanted = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if wanted.strip():
        return wanted
    return os.path.dirname(os.path.abspath(__file__))


def main():
    canvas = draw_front_page()
    png_bytes = encode_png(WIDTH, HEIGHT, canvas.pixels)
    out_dir = resolve_output_dir()
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, OUT_NAME)
    with open(out_path, "wb") as handle:
        handle.write(png_bytes)
    print("Wrote {} ({}x{}, {} bytes)".format(
        out_path, WIDTH, HEIGHT, len(png_bytes)))


if __name__ == "__main__":
    main()
