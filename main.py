"""news-image-20261120 — "Sum up 20 November's world news in one image".

A pure-Python-stdlib program that draws one 1024x1024 PNG summing up the
world news of Friday 20 November 2026 and writes it to /output/entry.png
(or $MAKEFUN_OUTPUT_DIR/entry.png outside the grader).

Design: a "night desk" storm chart. Ink-navy page, cream panels, the hero a
hand-drawn cyclone spiral over a stylised Bay of Bengal coastline, with the
day's other stories as captioned panels. No network, no randomness, no time:
two runs write byte-identical files.

Stories (all verified from public reporting on 20 Nov 2026; the 19 Nov
verdicts are tagged with their real date under the kicker "THE WORLD
REACTS"):
  - Cyclone Akvan makes landfall near Gopalpur, Odisha, at noon IST, 20 Nov.
  - Trump, Xi and Putin's first-ever trilateral (Shenzhen, 19 Nov) and its
    four-point declaration; the world reacts on 20 Nov.
  - ICJ finds Myanmar guilty of genocide against the Rohingya (19 Nov) —
    the first state ever found guilty of genocide.
  - South Korea's Supreme Court overturns ex-PM Han Duck-soo's 15-year
    sentence and orders a retrial (19 Nov).
  - Markets: Sensex +1.21%, Nifty +1.14%; Anthropic reportedly $1.5tn.
  - Culture/sport: Guardian Weekly inside Rockstar Edinburgh ahead of
    GTA VI; Women's Asian Hockey Trophy opens.

Run:  python3 main.py
Test: python3 -m unittest test_main -v
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# --- palette ---------------------------------------------------------------
NAVY = (14, 30, 51)        # page field
NAVY_DEEP = (10, 22, 38)   # hero sea
TEAL_SEA = (16, 58, 78)    # hero sea fill
TEAL_LAND = (32, 96, 84)   # stylised land
CREAM = (242, 239, 230)    # panels / masthead
CYAN = (127, 212, 232)     # storm spiral
CYAN_DIM = (74, 140, 165)  # waves
AMBER = (245, 165, 36)     # big numbers / accents
RED = (228, 87, 46)        # landfall / kickers
INK = (22, 32, 46)         # text on cream
WHITE = (255, 255, 255)
GREY = (120, 126, 138)     # secondary text

# --- 5x7 bitmap font (all caps + digits + punctuation) ----------------------
# Each glyph: 7 rows of 5 cells, '#' = on.
FONT = {
    " ": ["     "] * 7,
    "A": [" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "B": ["#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "],
    "C": [" ### ", "#   #", "#    ", "#    ", "#    ", "#   #", " ### "],
    "D": ["#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
    "F": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "],
    "G": [" ### ", "#   #", "#    ", "# ###", "#   #", "#   #", " ####"],
    "H": ["#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "I": [" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "J": ["  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "],
    "K": ["#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"],
    "M": ["#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "P": ["#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "],
    "Q": [" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"],
    "R": ["#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"],
    "S": [" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    "U": ["#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "V": ["#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "],
    "W": ["#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"],
    "X": ["#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"],
    "Y": ["#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "],
    "Z": ["#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"],
    "0": [" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "2": [" ### ", "#   #", "    #", "  ## ", " #   ", "#    ", "#####"],
    "3": ["#####", "   # ", "  #  ", "   # ", "    #", "#   #", " ### "],
    "4": ["   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "],
    "5": ["#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "],
    "6": ["  ## ", " #   ", "#    ", "#### ", "#   #", "#   #", " ### "],
    "7": ["#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "],
    "8": [" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "],
    "9": [" ### ", "#   #", "#   #", " ####", "    #", "   # ", " ##  "],
    ".": ["     ", "     ", "     ", "     ", "     ", " ##  ", " ##  "],
    ",": ["     ", "     ", "     ", "     ", " ##  ", "  #  ", " #   "],
    ":": ["     ", " ##  ", " ##  ", "     ", " ##  ", " ##  ", "     "],
    ";": ["     ", " ##  ", " ##  ", "     ", " ##  ", "  #  ", " #   "],
    "!": ["  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "     ", "  #  "],
    "?": [" ### ", "#   #", "    #", "  ## ", "  #  ", "     ", "  #  "],
    "'": ["  #  ", "  #  ", " #   ", "     ", "     ", "     ", "     "],
    "-": ["     ", "     ", "     ", " ### ", "     ", "     ", "     "],
    "(": ["   # ", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   # "],
    ")": [" #   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", " #   "],
    "/": ["    #", "   # ", "   # ", "  #  ", " #   ", " #   ", "#    "],
    "%": ["##  #", "## # ", "   # ", "  #  ", " #   ", "# ## ", "#  ##"],
    "+": ["     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "],
    "=": ["     ", "     ", "#####", "     ", "#####", "     ", "     "],
    "&": [" ##  ", "#  # ", "# #  ", " #   ", "# # #", "#  # ", " ## #"],
    '"': [" # # ", " # # ", "     ", "     ", "     ", "     ", "     "],
    "*": ["     ", "# # #", " ### ", "#####", " ### ", "# # #", "     "],
    "$": ["  #  ", " ####", "# #  ", " ### ", "  # #", "#### ", "  #  "],
}

# --- copy (every string drawn on the image; tests check font coverage) ------
MASTHEAD_TITLE = "THE WORLD IN ONE PICTURE"
MASTHEAD_DATE = "FRIDAY 20 NOVEMBER 2026"
MASTHEAD_SUB = "THE DAY'S WORLD NEWS IN A SINGLE IMAGE"
HERO_KICKER = "TODAY, 20 NOV - NOON IST"
HERO_HEAD1 = "AKVAN HITS"
HERO_HEAD2 = "ODISHA"
HERO_BODY = (
    "SEVERE CYCLONE AKVAN CROSSES THE ODISHA COAST AT NOON, WITH 90-100 KM/H "
    "WINDS AND 20-30 CM OF RAIN. SCHOOLS SHUT IN SIX DISTRICTS."
)
HERO_STAT1_NUM = "100,000+"
HERO_STAT1_LBL = "EVACUATED"
HERO_STAT2_NUM = "110 KM/H"
HERO_STAT2_LBL = "TOP GUSTS"
SEA_LABEL = "BAY OF BENGAL"
LAND_LABEL = "INDIA"
PLACE_LABEL = "GOPALPUR"
SUMMIT_KICKER = "THE WORLD REACTS - 19 NOV"
SUMMIT_HEAD = "THREE LEADERS, ONE TABLE"
SUMMIT_BODY = (
    "TRUMP, XI AND PUTIN MEET IN SHENZHEN AT THE APEC SUMMIT - THE FIRST "
    "EVER TRILATERAL OF THE THREE NUCLEAR POWERS - AND SIGN A FOUR-POINT "
    "DECLARATION."
)
SUMMIT_QUOTE = '"A NUCLEAR WAR CANNOT BE WON AND MUST NEVER BE FOUGHT"'
HAGUE_KICKER = "JUSTICE - 19 NOV, THE HAGUE"
HAGUE_HEAD1 = "MYANMAR GUILTY"
HAGUE_HEAD2 = "OF GENOCIDE"
HAGUE_BODY = (
    "THE WORLD COURT FINDS MYANMAR COMMITTED GENOCIDE AGAINST THE ROHINGYA "
    "IN 2017 - THE FIRST TIME ANY STATE HAS BEEN FOUND GUILTY. 1.2 MILLION "
    "REFUGEES WATCH FROM CAMPS IN BANGLADESH."
)
SEOUL_KICKER = "SEOUL - 19 NOV"
SEOUL_HEAD = "TOP COURT ORDERS RETRIAL"
SEOUL_BODY = (
    "EX-PM HAN DUCK-SOO'S 15-YEAR SENTENCE OVER THE 2024 MARTIAL LAW IS "
    "OVERTURNED. KIM KEON HEE'S 4-YEAR TERM UPHELD."
)
MARKETS_KICKER = "MARKETS + TECH"
MARKETS_HEAD = "SENSEX +1.21%"
MARKETS_BODY = (
    "INDIAN STOCKS RALLY AS THE NIFTY GAINS 1.14%. ANTHROPIC IS REPORTEDLY "
    "VALUED AT $1.5 TRILLION."
)
SPORT_KICKER = "SPORT + CULTURE"
SPORT_HEAD = "GTA VI: INSIDE ROCKSTAR"
SPORT_BODY = (
    "THE GUARDIAN WEEKLY GOES INSIDE THE EDINBURGH STUDIO AHEAD OF GTA VI. "
    "THE WOMEN'S ASIAN HOCKEY TROPHY OPENS."
)
FOOTER1 = "ALSO TODAY: FIJI DROUGHT DISASTER - COP31 IN TURKIYE"
FOOTER2 = "INDIA V NEW ZEALAND, 1ST TEST, WELLINGTON - DAY 2"

CONTENT_TEXT = "\n".join([
    MASTHEAD_TITLE, MASTHEAD_DATE, MASTHEAD_SUB,
    HERO_KICKER, HERO_HEAD1, HERO_HEAD2, HERO_BODY,
    HERO_STAT1_NUM, HERO_STAT1_LBL, HERO_STAT2_NUM, HERO_STAT2_LBL,
    SEA_LABEL, LAND_LABEL, PLACE_LABEL,
    SUMMIT_KICKER, SUMMIT_HEAD, SUMMIT_BODY, SUMMIT_QUOTE,
    HAGUE_KICKER, HAGUE_HEAD1, HAGUE_HEAD2, HAGUE_BODY,
    SEOUL_KICKER, SEOUL_HEAD, SEOUL_BODY,
    MARKETS_KICKER, MARKETS_HEAD, MARKETS_BODY,
    SPORT_KICKER, SPORT_HEAD, SPORT_BODY,
    FOOTER1, FOOTER2,
])


# --- canvas ------------------------------------------------------------------
class Canvas:
    def __init__(self, width=W, height=H):
        self.width = width
        self.height = height
        self.pixels = bytearray(NAVY * (width * height))

    def _idx(self, x, y):
        return (y * self.width + x) * 3

    def set(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = self._idx(x, y)
            self.pixels[i:i + 3] = bytes(colour)

    def pixel(self, x, y):
        i = self._idx(x, y)
        return tuple(self.pixels[i:i + 3])

    def fill_rect(self, x0, y0, x1, y1, colour):
        for y in range(max(0, y0), min(self.height, y1)):
            row = y * self.width * 3
            for x in range(max(0, x0), min(self.width, x1)):
                i = row + x * 3
                self.pixels[i:i + 3] = bytes(colour)

    def rect(self, x0, y0, x1, y1, colour, thickness=1):
        for t in range(thickness):
            self.fill_rect(x0 + t, y0 + t, x1 - t, y0 + t + 1, colour)
            self.fill_rect(x0 + t, y1 - t - 1, x1 - t, y1 - t, colour)
            self.fill_rect(x0 + t, y0 + t, x0 + t + 1, y1 - t, colour)
            self.fill_rect(x1 - t - 1, y0 + t, x1 - t, y1 - t, colour)

    def line(self, x0, y0, x1, y1, colour, thickness=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            half = thickness // 2
            self.fill_rect(x - half, y - half, x - half + thickness,
                           y - half + thickness, colour)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, colour, filled=False, thickness=1):
        if filled:
            for y in range(-r, r + 1):
                half = int(math.sqrt(max(0, r * r - y * y)))
                self.fill_rect(cx - half, cy + y, cx + half + 1, cy + y + 1, colour)
            return
        for t in range(thickness):
            rr = r - t
            steps = max(24, rr * 6)
            for i in range(steps):
                a = 2 * math.pi * i / steps
                self.set(int(cx + rr * math.cos(a)), int(cy + rr * math.sin(a)), colour)

    def arc(self, cx, cy, r, a0, a1, colour, thickness=2):
        steps = max(8, int(r * (a1 - a0)))
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            self.fill_rect(int(cx + r * math.cos(a)) - thickness // 2,
                           int(cy + r * math.sin(a)) - thickness // 2,
                           int(cx + r * math.cos(a)) - thickness // 2 + thickness,
                           int(cy + r * math.sin(a)) - thickness // 2 + thickness,
                           colour)

    def poly_fill(self, points, colour):
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(int(x0 + (y - y0) * (x1 - x0) / (y1 - y0)))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(xs[i], y, xs[i + 1] + 1, y + 1, colour)

    def polyline(self, points, colour, thickness=1):
        for i in range(len(points) - 1):
            self.line(points[i][0], points[i][1],
                      points[i + 1][0], points[i + 1][1], colour, thickness)


# --- text --------------------------------------------------------------------
def text_width(text, scale):
    return len(text) * 6 * scale


def draw_text(cv, x, y, text, scale, colour):
    for ci, ch in enumerate(text):
        glyph = FONT.get(ch)
        if glyph is None:
            continue
        ox = x + ci * 6 * scale
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == "#":
                    cv.fill_rect(ox + col * scale, y + row * scale,
                                 ox + (col + 1) * scale, y + (row + 1) * scale,
                                 colour)


def draw_text_centered(cv, cx, y, text, scale, colour):
    draw_text(cv, cx - text_width(text, scale) // 2, y, text, scale, colour)


def wrap_text(text, scale, max_width):
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_block(cv, x, y, text, scale, colour, max_width, line_gap=4):
    lines = wrap_text(text, scale, max_width)
    for i, line in enumerate(lines):
        draw_text(cv, x, y + i * (7 * scale + line_gap), line, scale, colour)
    return y + len(lines) * (7 * scale + line_gap)


# --- artwork -----------------------------------------------------------------
def draw_storm(cv, x0, y0, x1, y1):
    """Cyclone Akvan over a stylised Bay of Bengal coastline."""
    cv.fill_rect(x0, y0, x1, y1, TEAL_SEA)
    # stylised east coast of India (land on the right)
    coast = [(470, y0), (x1, y0), (x1, y1), (500, y1), (478, 470),
             (492, 400), (462, 330), (478, 260), (452, 200), (470, y0)]
    cv.poly_fill(coast, TEAL_LAND)
    cv.polyline([(470, y0), (452, 200), (478, 260), (462, 330),
                 (492, 400), (478, 470), (500, y1)], CREAM, 2)
    # sea waves
    for wy in (180, 210, 470, 500):
        cv.polyline([(x0 + 30, wy), (x0 + 90, wy - 8), (x0 + 150, wy),
                     (x0 + 210, wy - 8), (x0 + 260, wy)], CYAN_DIM, 2)
    # cyclone spiral: broken concentric rings, offset per ring
    cx, cy = 260, 330
    for r, off in ((88, 0.0), (70, 0.5), (52, 1.0), (36, 1.5), (20, 2.0)):
        cv.arc(cx, cy, r, off, off + 4.4, CYAN, 4)
        cv.arc(cx, cy, r, off + 4.9, off + 5.9, WHITE, 3)
    cv.circle(cx, cy, 12, NAVY_DEEP, filled=True)
    cv.circle(cx, cy, 12, CYAN, thickness=2)
    # landfall marker on the coast
    lx, ly = 466, 330
    cv.circle(lx, ly, 13, RED, filled=True)
    cv.circle(lx, ly, 13, WHITE, thickness=2)
    cv.circle(lx, ly, 5, WHITE, filled=True)
    cv.line(450, 309, 460, 324, WHITE, 2)
    draw_text(cv, 352, 300, PLACE_LABEL, 2, WHITE)
    draw_text(cv, x0 + 22, y0 + 18, SEA_LABEL, 2, CYAN)
    draw_text(cv, 505, 180, LAND_LABEL, 2, CREAM)


def draw_flags(cv, x, y):
    """Three small flags: US, China, Russia."""
    # US: stripes + blue canton
    cv.fill_rect(x, y, x + 64, y + 40, WHITE)
    for i in range(7):
        if i % 2 == 0:
            cv.fill_rect(x, y + i * 6, x + 64, y + i * 6 + 6, RED)
    cv.fill_rect(x, y, x + 26, y + 21, (30, 50, 110))
    for sy in (5, 12, 19):
        for sx in (5, 13, 21):
            cv.set(x + sx, y + sy, WHITE)
    # China: red + yellow stars
    cv.fill_rect(x + 76, y, x + 140, y + 40, (222, 41, 16))
    cv.circle(x + 88, y + 12, 5, AMBER, filled=True)
    for sx, sy in ((104, 8), (112, 14), (112, 22), (104, 28)):
        cv.circle(x + sx, y + sy, 2, AMBER, filled=True)
    # Russia: white / blue / red tricolour
    cv.fill_rect(x + 152, y, x + 216, y + 40, WHITE)
    cv.fill_rect(x + 152, y + 13, x + 216, y + 27, (0, 70, 160))
    cv.fill_rect(x + 152, y + 27, x + 216, y + 40, RED)


def draw_scales(cv, cx, top):
    """Simple scales of justice."""
    cv.line(cx, top, cx, top + 64, AMBER, 3)
    cv.line(cx - 34, top + 8, cx + 34, top + 8, AMBER, 3)
    cv.circle(cx, top - 4, 5, AMBER, thickness=2)
    for sx in (cx - 34, cx + 34):
        cv.line(sx, top + 8, sx - 14, top + 38, AMBER, 2)
        cv.line(sx, top + 8, sx + 14, top + 38, AMBER, 2)
        cv.arc(sx, top + 38, 14, 0.15, math.pi - 0.15, AMBER, 3)
        cv.line(sx - 14, top + 38, sx + 14, top + 38, AMBER, 2)


# --- layout ------------------------------------------------------------------
def build_canvas():
    cv = Canvas()
    # thin cream frame
    cv.rect(8, 8, 1016, 1016, CREAM, 2)

    # ---- masthead: cream band --------------------------------------------
    cv.fill_rect(24, 24, 1000, 120, CREAM)
    draw_text_centered(cv, 512, 34, MASTHEAD_TITLE, 5, INK)
    draw_text_centered(cv, 512, 76, MASTHEAD_DATE, 3, RED)
    draw_text_centered(cv, 512, 100, MASTHEAD_SUB, 1, GREY)
    cv.fill_rect(24, 120, 1000, 124, AMBER)

    # ---- hero -------------------------------------------------------------
    cv.fill_rect(24, 132, 1000, 548, CREAM)
    draw_storm(cv, 36, 144, 592, 536)
    hx = 612
    draw_text(cv, hx, 150, HERO_KICKER, 2, RED)
    draw_text(cv, hx, 178, HERO_HEAD1, 5, INK)
    draw_text(cv, hx, 216, HERO_HEAD2, 5, INK)
    y = draw_block(cv, hx, 262, HERO_BODY, 2, INK, 376, line_gap=5)
    cv.fill_rect(hx, y + 8, 988, y + 10, AMBER)
    y += 22
    draw_text(cv, hx, y, HERO_STAT1_NUM, 4, AMBER)
    draw_text(cv, hx + text_width(HERO_STAT1_NUM, 4) + 8, y + 8,
              HERO_STAT1_LBL, 2, INK)
    draw_text(cv, hx, y + 40, HERO_STAT2_NUM, 4, AMBER)
    draw_text(cv, hx + text_width(HERO_STAT2_NUM, 4) + 8, y + 48,
              HERO_STAT2_LBL, 2, INK)

    # ---- middle band: summit + hague --------------------------------------
    # summit panel
    cv.fill_rect(24, 560, 500, 796, CREAM)
    draw_text(cv, 40, 572, SUMMIT_KICKER, 2, RED)
    draw_text(cv, 40, 594, SUMMIT_HEAD, 3, INK)
    draw_flags(cv, 40, 622)
    y = draw_block(cv, 40, 670, SUMMIT_BODY, 2, INK, 444, line_gap=4)
    draw_block(cv, 40, y + 6, SUMMIT_QUOTE, 2, RED, 444, line_gap=4)
    # hague panel
    cv.fill_rect(524, 560, 1000, 796, CREAM)
    draw_text(cv, 540, 576, HAGUE_KICKER, 2, RED)
    draw_text(cv, 540, 600, HAGUE_HEAD1, 4, INK)
    draw_text(cv, 540, 632, HAGUE_HEAD2, 4, INK)
    draw_scales(cv, 920, 604)
    draw_block(cv, 540, 668, HAGUE_BODY, 2, INK, 444, line_gap=4)

    # ---- bottom band: three small panels ----------------------------------
    panels = [
        (24, 344, SEOUL_KICKER, SEOUL_HEAD, SEOUL_BODY),
        (356, 676, MARKETS_KICKER, MARKETS_HEAD, MARKETS_BODY),
        (688, 1000, SPORT_KICKER, SPORT_HEAD, SPORT_BODY),
    ]
    for x0, x1, kicker, head, body in panels:
        cv.fill_rect(x0, 808, x1, 952, CREAM)
        draw_text(cv, x0 + 16, 822, kicker, 2, RED)
        y = draw_block(cv, x0 + 16, 846, head, 3, INK, x1 - x0 - 32, line_gap=3)
        draw_block(cv, x0 + 16, y + 6, body, 1, INK, x1 - x0 - 32, line_gap=3)

    # ---- footer ------------------------------------------------------------
    draw_text_centered(cv, 512, 966, FOOTER1, 2, CREAM)
    draw_text_centered(cv, 512, 986, FOOTER2, 2, AMBER)
    return cv


def encode_png(cv):
    raw = bytearray()
    for y in range(cv.height):
        raw.append(0)  # filter: none
        start = y * cv.width * 3
        raw += cv.pixels[start:start + cv.width * 3]

    def chunk(ctype, data):
        out = struct.pack(">I", len(data)) + ctype + data
        out += struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.width, cv.height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = build_canvas()
    data = encode_png(cv)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
