#!/usr/bin/env python3
"""The World in One Day - Friday 27 November 2026.

News-image entry for make.fun competition news-image-20261127.
Pure Python 3.13 standard library only. No network, no external files:
the program draws everything itself (a tiny 5x7 bitmap font defined below,
flat vector-style illustrations) and writes /output/entry.png (or
$MAKEFUN_OUTPUT_DIR/entry.png). Deterministic: two runs write identical bytes.

Layout (1024x1024):
  header  -> hero (Thanksgiving storm) -> 12 illustrated story cards (3x4)
  -> timeline strip (UTC) -> day-in-numbers strip -> also-on + world map
  -> footer date check.
"""

import binascii
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
INK = (20, 20, 26)
PAPER = (244, 239, 230)
NAVY = (13, 27, 51)
NAVY2 = (24, 46, 82)
RED = (192, 57, 43)
BLUE = (31, 95, 168)
TEAL = (15, 130, 125)
AMBER = (214, 138, 20)
GREEN = (39, 130, 74)
PURPLE = (110, 72, 160)
WHITE = (255, 255, 255)
CREAM = (250, 246, 238)
LIGHT = (226, 231, 238)
MIDGREY = (120, 126, 138)
DARKGREY = (70, 74, 84)
SKY = (168, 205, 232)
SKYDARK = (96, 130, 168)
ORANGE = (232, 110, 30)
FLAME = (245, 158, 40)
SMOKE = (90, 90, 96)
GOLD = (201, 162, 39)

# ------------------------------------------------------- 5x7 bitmap font
# Each glyph: 7 rows of 5 bits, '#' = on. Uppercase + digits + punctuation.
# Text is rendered uppercased; the font is drawn by this program itself.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    ">": ("10000", "01000", "00100", "00010", "00100", "01000", "10000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
}

# Euro sign drawn as its own glyph (not in FONT, used as "EUR" fallback).
EURO = ("00111", "01000", "10000", "11110", "10000", "01000", "00111")


def text_w(s, scale):
    """Pixel width of string s at given scale (6 px advance per char)."""
    return len(s) * 6 * scale


def draw_text(cv, x, y, s, scale, color):
    """Draw uppercased text with the built-in 5x7 font. Returns width."""
    s = s.upper()
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g is None:
            if ch == "\u20ac":  # euro sign
                g = EURO
            else:
                cx += 6 * scale
                continue
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == "1":
                    fill_rect(cv, cx + col * scale, y + row * scale,
                              scale, scale, color)
        cx += 6 * scale
    return cx - x


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns list of lines fitting max_w pixels."""
    words = s.upper().split(" ")
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_text_block(cv, x, y, s, scale, color, max_w, line_h=None):
    """Draw wrapped text; returns y after the last line."""
    if line_h is None:
        line_h = 9 * scale
    for line in wrap_text(s, scale, max_w):
        draw_text(cv, x, y, line, scale, color)
        y += line_h
    return y


# ------------------------------------------------------------- raster core
def new_canvas(w, h, color):
    cv = bytearray(w * h * 3)
    r, g, b = color
    for i in range(0, len(cv), 3):
        cv[i] = r
        cv[i + 1] = g
        cv[i + 2] = b
    return cv


def set_px(cv, x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        cv[i], cv[i + 1], cv[i + 2] = color


def fill_rect(cv, x, y, w, h, color):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    r, g, b = color
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            cv[i] = r
            cv[i + 1] = g
            cv[i + 2] = b


def draw_rect_outline(cv, x, y, w, h, color, t=1):
    fill_rect(cv, x, y, w, t, color)
    fill_rect(cv, x, y + h - t, w, t, color)
    fill_rect(cv, x, y, t, h, color)
    fill_rect(cv, x + w - t, y, t, h, color)


def draw_line(cv, x0, y0, x1, y1, color, t=1):
    """Bresenham line with square thickness t."""
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    half = t // 2
    while True:
        fill_rect(cv, x0 - half, y0 - half, t, t, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def fill_circle(cv, cx, cy, r, color):
    for dy in range(-r, r + 1):
        span = int((r * r - dy * dy) ** 0.5)
        fill_rect(cv, cx - span, cy + dy, span * 2 + 1, 1, color)


def draw_circle_outline(cv, cx, cy, r, color, t=1):
    for a in range(0, 360, 2):
        import math
        x = cx + int(r * math.cos(math.radians(a)))
        y = cy + int(r * math.sin(math.radians(a)))
        fill_rect(cv, x - t // 2, y - t // 2, t, t, color)


def fill_ellipse(cv, cx, cy, rx, ry, color):
    for dy in range(-ry, ry + 1):
        span = int(rx * (1 - (dy * dy) / float(ry * ry)) ** 0.5) if ry else 0
        fill_rect(cv, cx - span, cy + dy, span * 2 + 1, 1, color)


def fill_poly(cv, pts, color):
    """Scanline polygon fill (pts = list of (x, y))."""
    if len(pts) < 3:
        return
    ys = [p[1] for p in pts]
    for y in range(max(0, min(ys)), min(H, max(ys) + 1)):
        xs = []
        n = len(pts)
        for i in range(n):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                if y1 != y0:
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for k in range(0, len(xs) - 1, 2):
            fill_rect(cv, int(xs[k]), y, max(1, int(xs[k + 1]) - int(xs[k])), 1, color)


def round_rect(cv, x, y, w, h, r, color):
    fill_rect(cv, x + r, y, w - 2 * r, h, color)
    fill_rect(cv, x, y + r, w, h - 2 * r, color)
    fill_circle(cv, x + r, y + r, r, color)
    fill_circle(cv, x + w - r - 1, y + r, r, color)
    fill_circle(cv, x + r, y + h - r - 1, r, color)
    fill_circle(cv, x + w - r - 1, y + h - r - 1, r, color)


def round_rect_outline(cv, x, y, w, h, r, color, t=1):
    draw_line(cv, x + r, y, x + w - r, y, color, t)
    draw_line(cv, x + r, y + h - 1, x + w - r, y + h - 1, color, t)
    draw_line(cv, x, y + r, x, y + h - r, color, t)
    draw_line(cv, x + w - 1, y + r, x + w - 1, y + h - r, color, t)
    for (cx, cy) in ((x + r, y + r), (x + w - r - 1, y + r),
                     (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
        draw_circle_outline(cv, cx, cy, r, color, t)


# ------------------------------------------------------------- PNG encoder
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw.extend(cv[y * W * 3:(y + 1) * W * 3])
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ------------------------------------------------------- shared draw bits
def chip(cv, x, y, label, fg, bg):
    """Small rounded status chip; returns width used."""
    s = 1
    pad = 4
    w = text_w(label, s) + pad * 2
    h = 13
    round_rect(cv, x, y, w, h, 6, bg)
    draw_text(cv, x + pad, y + 3, label, s, fg)
    return w


def status_dot(cv, x, y, color):
    fill_circle(cv, x, y, 4, color)
    draw_circle_outline(cv, x, y, 4, WHITE, 1)


def flame(cv, x, y, s):
    """Stylised flame, base at (x, y), height ~s."""
    fill_poly(cv, [(x, y), (x - int(0.42 * s), y - int(0.45 * s)),
                   (x - int(0.18 * s), y - int(0.75 * s)),
                   (x + int(0.10 * s), y - int(0.55 * s)),
                   (x + int(0.30 * s), y - s),
                   (x + int(0.42 * s), y - int(0.45 * s))], ORANGE)
    fill_poly(cv, [(x, y), (x - int(0.20 * s), y - int(0.30 * s)),
                   (x, y - int(0.55 * s)),
                   (x + int(0.20 * s), y - int(0.25 * s))], FLAME)


def smoke(cv, x, y, r, color=SMOKE):
    fill_circle(cv, x, y, r, color)
    fill_circle(cv, x + int(r * 0.8), y - int(r * 0.5), int(r * 0.75), color)
    fill_circle(cv, x - int(r * 0.8), y - int(r * 0.4), int(r * 0.7), color)


def cloud(cv, x, y, s, color):
    fill_ellipse(cv, x, y, int(1.6 * s), int(0.7 * s), color)
    fill_circle(cv, x - int(0.7 * s), y - int(0.2 * s), int(0.7 * s), color)
    fill_circle(cv, x + int(0.6 * s), y - int(0.3 * s), int(0.8 * s), color)


def rain(cv, x, y, w, h, color, step=16):
    for rx in range(x, x + w, step):
        draw_line(cv, rx, y, rx - 6, y + 12, color, 2)


def bolt(cv, x, y, s, color=FLAME):
    fill_poly(cv, [(x, y), (x - int(0.25 * s), y + int(0.55 * s)),
                   (x + int(0.05 * s), y + int(0.55 * s)),
                   (x - int(0.15 * s), y + s),
                   (x + int(0.30 * s), y + int(0.40 * s)),
                   (x, y + int(0.40 * s))], color)


def building(cv, x, y, w, h, color, win=LIGHT):
    fill_rect(cv, x, y, w, h, color)
    for wy in range(y + 6, y + h - 4, 12):
        for wx in range(x + 5, x + w - 5, 11):
            fill_rect(cv, wx, wy, 6, 7, win)


# ------------------------------------------------------------ illustrations
def ill_hero_storm(cv, x, y, w, h):
    """Thanksgiving nor'easter over New York: dark sky, rain, wind,
    a deflated parade balloon on the ground, leaning power pole."""
    fill_rect(cv, x, y, w, h, NAVY2)
    # skyline
    fill_rect(cv, x, y + h - 46, w, 46, (16, 30, 56))
    building(cv, x + 12, y + h - 96, 46, 96, (22, 40, 70))
    building(cv, x + 66, y + h - 78, 38, 78, (18, 34, 62))
    building(cv, x + 330, y + h - 110, 52, 110, (22, 40, 70))
    building(cv, x + 390, y + h - 84, 40, 84, (18, 34, 62))
    # storm clouds
    cloud(cv, x + 90, y + 26, 34, (52, 66, 92))
    cloud(cv, x + 250, y + 16, 40, (44, 58, 84))
    cloud(cv, x + 400, y + 30, 30, (52, 66, 92))
    # lightning
    bolt(cv, x + 300, y + 40, 46)
    bolt(cv, x + 150, y + 58, 34, (245, 200, 60))
    # rain
    rain(cv, x + 6, y + 60, w - 12, 60, (150, 180, 210))
    # street
    fill_rect(cv, x, y + h - 34, w, 34, (40, 44, 54))
    draw_line(cv, x, y + h - 17, x + w, y + h - 17, (230, 200, 60), 2)
    # leaning power pole with sparking wire
    draw_line(cv, x + 200, y + h - 34, x + 214, y + h - 118, (60, 46, 32), 5)
    draw_line(cv, x + 196, y + h - 104, x + 232, y + h - 104, (60, 46, 32), 4)
    draw_line(cv, x + 232, y + h - 104, x + 268, y + h - 78, (200, 200, 210), 2)
    fill_circle(cv, x + 252, y + h - 90, 4, FLAME)
    fill_circle(cv, x + 258, y + h - 84, 3, (245, 200, 60))
    # deflated balloon on the ground (red, sagging)
    fill_ellipse(cv, x + 330, y + h - 46, 52, 13, RED)
    fill_ellipse(cv, x + 330, y + h - 52, 34, 8, (210, 80, 60))
    draw_line(cv, x + 300, y + h - 44, x + 288, y + h - 34, (210, 80, 60), 3)
    # fallen tree branch
    draw_line(cv, x + 30, y + h - 34, x + 62, y + h - 52, (60, 46, 32), 4)
    fill_circle(cv, x + 60, y + h - 54, 10, (30, 110, 60))
    fill_circle(cv, x + 48, y + h - 48, 8, (36, 128, 70))


def ill_bangkok(cv, x, y, w, h):
    """Bangchak refinery: towers, tanks, flame + black smoke."""
    fill_rect(cv, x, y, w, h, (232, 214, 178))
    fill_rect(cv, x, y + h - 18, w, 18, (120, 110, 96))
    # storage tanks
    fill_ellipse(cv, x + 26, y + h - 52, 22, 7, (200, 200, 205))
    fill_rect(cv, x + 4, y + h - 52, 44, 34, (210, 210, 214))
    fill_ellipse(cv, x + 26, y + h - 52, 22, 7, (228, 228, 232))
    fill_ellipse(cv, x + 66, y + h - 48, 18, 6, (200, 200, 205))
    fill_rect(cv, x + 48, y + h - 48, 36, 30, (210, 210, 214))
    # distillation tower
    fill_rect(cv, x + 128, y + 8, 26, h - 26, (150, 158, 168))
    fill_rect(cv, x + 122, y + 16, 38, 5, (120, 128, 138))
    fill_rect(cv, x + 122, y + 34, 38, 5, (120, 128, 138))
    fill_rect(cv, x + 122, y + 52, 38, 5, (120, 128, 138))
    # pipes
    draw_line(cv, x + 84, y + h - 18, x + 128, y + h - 30, (110, 118, 128), 4)
    # flame + smoke
    flame(cv, x + 186, y + h - 20, 52)
    flame(cv, x + 210, y + h - 20, 36)
    smoke(cv, x + 196, y + 18, 12, (70, 70, 76))
    smoke(cv, x + 210, y + 6, 9, (80, 80, 86))


def ill_cairo(cv, x, y, w, h):
    """Cairo ring road: overturned tanker, huge fire, night sky."""
    fill_rect(cv, x, y, w, h, (30, 34, 52))
    fill_circle(cv, x + 200, y + 16, 10, (240, 220, 160))
    # distant city lights
    for bx in range(x + 8, x + w - 8, 26):
        fill_rect(cv, bx, y + h - 66, 16, 18, (44, 48, 70))
        fill_rect(cv, bx + 4, y + h - 62, 3, 3, (245, 200, 60))
        fill_rect(cv, bx + 10, y + h - 58, 3, 3, (245, 200, 60))
    # road
    fill_rect(cv, x, y + h - 26, w, 26, (52, 52, 58))
    draw_line(cv, x, y + h - 13, x + w, y + h - 13, (230, 200, 60), 2)
    # overturned tanker (on its side)
    fill_ellipse(cv, x + 96, y + h - 44, 46, 16, (190, 60, 40))
    fill_rect(cv, x + 150, y + h - 52, 26, 20, (150, 40, 30))
    fill_circle(cv, x + 66, y + h - 30, 7, INK)
    fill_circle(cv, x + 128, y + h - 30, 7, INK)
    # big flame
    flame(cv, x + 96, y + h - 52, 64)
    flame(cv, x + 130, y + h - 52, 44)
    smoke(cv, x + 110, y + 14, 13)
    smoke(cv, x + 140, y + 4, 10)


def ill_gaza(cv, x, y, w, h):
    """Gaza City at night: damaged apartment block, smoke, searchlight."""
    fill_rect(cv, x, y, w, h, (24, 28, 46))
    fill_circle(cv, x + 30, y + 18, 9, (240, 220, 160))
    # skyline blocks
    building(cv, x + 8, y + 30, 44, h - 48, (52, 56, 78))
    building(cv, x + 60, y + 44, 40, h - 62, (44, 48, 68))
    building(cv, x + 170, y + 36, 48, h - 54, (52, 56, 78))
    # damaged block (broken top, exposed floors)
    fill_rect(cv, x + 106, y + 22, 58, h - 40, (70, 60, 66))
    fill_poly(cv, [(x + 106, y + 22), (x + 130, y + 34), (x + 146, y + 22),
                   (x + 164, y + 30), (x + 164, y + 40), (x + 106, y + 40)],
              (40, 36, 40))
    for wy in range(y + 44, y + h - 24, 12):
        fill_rect(cv, x + 114, wy, 14, 7, (245, 200, 60))
        fill_rect(cv, x + 140, wy, 14, 7, (230, 180, 90))
    # smoke + sparks
    smoke(cv, x + 136, y + 12, 11)
    fill_circle(cv, x + 150, y + 46, 3, FLAME)
    fill_circle(cv, x + 120, y + 58, 2, (245, 200, 60))


def ill_ukraine(cv, x, y, w, h):
    """Power grid under attack: pylon, lightning, dark sky, sparks."""
    fill_rect(cv, x, y, w, h, (28, 42, 66))
    cloud(cv, x + 60, y + 12, 26, (58, 74, 100))
    cloud(cv, x + 180, y + 8, 22, (50, 66, 92))
    # pylon
    draw_line(cv, x + 110, y + h - 16, x + 122, y + 26, (200, 205, 215), 4)
    draw_line(cv, x + 134, y + h - 16, x + 122, y + 26, (200, 205, 215), 4)
    draw_line(cv, x + 96, y + 34, x + 148, y + 34, (200, 205, 215), 4)
    draw_line(cv, x + 104, y + 48, x + 140, y + 48, (200, 205, 215), 3)
    draw_line(cv, x + 110, y + h - 16, x + 134, y + h - 16, (200, 205, 215), 3)
    # sagging power lines
    draw_line(cv, x + 96, y + 34, x + 20, y + 52, (220, 220, 225), 2)
    draw_line(cv, x + 148, y + 34, x + 226, y + 52, (220, 220, 225), 2)
    # lightning + sparks
    bolt(cv, x + 176, y + 30, 40)
    fill_circle(cv, x + 108, y + 60, 3, FLAME)
    fill_circle(cv, x + 136, y + 66, 2, (245, 200, 60))
    # ground + warning sign
    fill_rect(cv, x, y + h - 16, w, 16, (40, 52, 40))
    fill_poly(cv, [(x + 196, y + h - 44), (x + 214, y + h - 44),
                   (x + 205, y + h - 62)], (245, 200, 60))
    draw_text(cv, x + 202, y + h - 56, "!", 1, INK)


def ill_eu(cv, x, y, w, h):
    """EU budget: circle of gold stars on blue, coins + deadlock bars."""
    fill_rect(cv, x, y, w, h, (28, 52, 120))
    import math
    cx, cy, r = x + 82, y + 42, 26
    for k in range(12):
        a = math.radians(k * 30 - 90)
        sx = cx + int(r * math.cos(a))
        sy = cy + int(r * math.sin(a))
        fill_circle(cv, sx, sy, 3, GOLD)
    fill_circle(cv, cx, cy, 12, GOLD)
    draw_text(cv, cx - 6, cy - 5, "E", 2, (28, 52, 120))
    # coins stack
    for i, xx in enumerate((x + 158, x + 176, x + 194)):
        fill_ellipse(cv, xx, y + h - 30 - i * 4, 14, 5, GOLD)
        fill_rect(cv, xx - 14, y + h - 30 - i * 4, 28, 6, (180, 142, 30))
    # deadlock: two opposing arrows
    draw_line(cv, x + 150, y + 26, x + 196, y + 26, WHITE, 3)
    draw_line(cv, x + 196, y + 26, x + 186, y + 20, WHITE, 3)
    draw_line(cv, x + 196, y + 26, x + 186, y + 32, WHITE, 3)
    draw_line(cv, x + 216, y + 40, x + 170, y + 40, (245, 120, 90), 3)
    draw_line(cv, x + 170, y + 40, x + 180, y + 34, (245, 120, 90), 3)
    draw_line(cv, x + 170, y + 40, x + 180, y + 46, (245, 120, 90), 3)


def ill_hormuz(cv, x, y, w, h):
    """Strait of Hormuz: sea, two tankers, mine explosion."""
    fill_rect(cv, x, y, w, h, (126, 190, 220))
    fill_rect(cv, x, y, w, 26, (168, 205, 232))
    cloud(cv, x + 50, y + 10, 20, WHITE)
    cloud(cv, x + 180, y + 14, 16, WHITE)
    # sea waves
    for wy in (y + 56, y + 72):
        for wx in range(x, x + w, 24):
            draw_line(cv, wx, wy, wx + 12, wy, (255, 255, 255), 2)
    # tanker 1
    fill_rect(cv, x + 14, y + h - 34, 96, 14, (160, 40, 32))
    fill_rect(cv, x + 88, y + h - 52, 16, 20, WHITE)
    fill_rect(cv, x + 92, y + h - 60, 4, 10, (120, 40, 30))
    # tanker 2 (burning)
    fill_rect(cv, x + 140, y + h - 34, 88, 14, (60, 60, 70))
    fill_rect(cv, x + 196, y + h - 50, 14, 18, WHITE)
    flame(cv, x + 168, y + h - 34, 40)
    flame(cv, x + 190, y + h - 34, 28)
    smoke(cv, x + 178, y + 22, 10)
    # mine in the water
    fill_circle(cv, x + 120, y + h - 22, 6, INK)
    for dx, dy in ((-7, 0), (7, 0), (0, -7), (0, 7), (-5, -5), (5, 5)):
        draw_line(cv, x + 120, y + h - 22, x + 120 + dx, y + h - 22 + dy, INK, 2)


def ill_korea(cv, x, y, w, h):
    """North Korea: missile launch, mountains, red star."""
    fill_rect(cv, x, y, w, h, (214, 226, 240))
    # mountains
    fill_poly(cv, [(x, y + h - 18), (x + 50, y + 26), (x + 100, y + h - 18)],
              (90, 120, 150))
    fill_poly(cv, [(x + 80, y + h - 18), (x + 150, y + 12),
                   (x + 220, y + h - 18)], (70, 100, 132))
    fill_poly(cv, [(x + 40, y + 36), (x + 50, y + 26), (x + 60, y + 36)],
              WHITE)
    fill_poly(cv, [(x + 140, y + 22), (x + 150, y + 12), (x + 160, y + 22)],
              WHITE)
    fill_rect(cv, x, y + h - 18, w, 18, (60, 90, 70))
    # missile
    fill_poly(cv, [(x + 118, y + 8), (x + 126, y + 8), (x + 126, y + 34),
                   (x + 118, y + 34)], (230, 230, 235))
    fill_poly(cv, [(x + 118, y + 8), (x + 122, y - 2), (x + 126, y + 8)],
              RED)
    fill_poly(cv, [(x + 118, y + 34), (x + 110, y + 44), (x + 118, y + 40)],
              RED)
    fill_poly(cv, [(x + 126, y + 34), (x + 134, y + 44), (x + 126, y + 40)],
              RED)
    flame(cv, x + 122, y + 44, 26)
    # red star
    fill_circle(cv, x + 200, y + 18, 10, RED)
    draw_text(cv, x + 195, y + 11, "*", 1, WHITE)


def ill_cologne(cv, x, y, w, h):
    """Cologne: cathedral twin spires + police shield."""
    fill_rect(cv, x, y, w, h, (196, 214, 228))
    cloud(cv, x + 60, y + 12, 20, WHITE)
    cloud(cv, x + 180, y + 18, 16, WHITE)
    # cathedral
    fill_rect(cv, x + 20, y + 30, 34, h - 48, (70, 74, 84))
    fill_poly(cv, [(x + 20, y + 30), (x + 37, y + 2), (x + 54, y + 30)],
              (52, 56, 66))
    fill_rect(cv, x + 62, y + 30, 34, h - 48, (70, 74, 84))
    fill_poly(cv, [(x + 62, y + 30), (x + 79, y + 2), (x + 96, y + 30)],
              (52, 56, 66))
    fill_rect(cv, x + 54, y + 52, 8, h - 70, (60, 64, 74))
    for wy in range(y + 58, y + h - 30, 14):
        fill_rect(cv, x + 30, wy, 12, 8, (245, 200, 60))
        fill_rect(cv, x + 74, wy, 12, 8, (245, 200, 60))
    fill_rect(cv, x, y + h - 18, w, 18, (110, 118, 110))
    # police shield
    fill_poly(cv, [(x + 168, y + 34), (x + 200, y + 34), (x + 200, y + 56),
                   (x + 184, y + 72), (x + 168, y + 56)], BLUE)
    draw_text(cv, x + 180, y + 42, "*", 2, WHITE)
    draw_line(cv, x + 168, y + 44, x + 200, y + 44, WHITE, 2)


def ill_uk(cv, x, y, w, h):
    """UK migration: Big Ben + falling chart arrow."""
    fill_rect(cv, x, y, w, h, (196, 220, 232))
    # Big Ben tower
    fill_rect(cv, x + 24, y + 18, 30, h - 36, (90, 70, 50))
    fill_poly(cv, [(x + 24, y + 18), (x + 39, y + 2), (x + 54, y + 18)],
              (70, 52, 36))
    fill_circle(cv, x + 39, y + 34, 11, CREAM)
    draw_line(cv, x + 39, y + 34, x + 39, y + 26, INK, 2)
    draw_line(cv, x + 39, y + 34, x + 45, y + 34, INK, 2)
    # chart: falling bars + arrow
    bars = [46, 38, 30, 22]
    for i, bh in enumerate(bars):
        fill_rect(cv, x + 84 + i * 36, y + h - 24 - bh, 24, bh,
                  (31, 95, 168) if i < 3 else GREEN)
    draw_line(cv, x + 84, y + h - 70, x + 216, y + h - 40, RED, 3)
    draw_line(cv, x + 216, y + h - 40, x + 202, y + h - 42, RED, 3)
    draw_line(cv, x + 216, y + h - 40, x + 214, y + h - 54, RED, 3)


def ill_argentina(cv, x, y, w, h):
    """Argentina: congress dome + ballot box."""
    fill_rect(cv, x, y, w, h, (168, 205, 235))
    cloud(cv, x + 60, y + 10, 20, WHITE)
    # congress building
    fill_rect(cv, x + 20, y + 46, 120, h - 64, (240, 236, 224))
    fill_rect(cv, x + 14, y + h - 22, 132, 6, (200, 196, 184))
    for cx in range(x + 28, x + 132, 20):
        fill_rect(cv, cx, y + 62, 8, h - 84, (180, 176, 164))
    fill_ellipse(cv, x + 80, y + 18, 34, 26, (110, 170, 210))
    fill_rect(cv, x + 78, y + 40, 4, 8, (110, 170, 210))
    # ballot box
    fill_rect(cv, x + 168, y + h - 46, 52, 28, (31, 95, 168))
    fill_rect(cv, x + 164, y + h - 52, 60, 8, (24, 76, 138))
    fill_rect(cv, x + 186, y + h - 56, 16, 5, WHITE)
    # ballot slip going in
    fill_poly(cv, [(x + 182, y + h - 66), (x + 200, y + h - 66),
                   (x + 196, y + h - 56), (x + 186, y + h - 56)], WHITE)
    draw_text(cv, x + 186, y + h - 62, "X", 1, BLUE)


def ill_chess(cv, x, y, w, h):
    """World chess: board, king + queen, draw handshake flag."""
    fill_rect(cv, x, y, w, h, (222, 206, 178))
    # board 8x8 mini (each cell 9px) centred left
    bx, by, cell = x + 12, y + 8, 9
    for r in range(8):
        for c in range(8):
            col = CREAM if (r + c) % 2 == 0 else (60, 48, 36)
            fill_rect(cv, bx + c * cell, by + r * cell, cell, cell, col)
    # king + queen pieces on the board
    fill_circle(cv, bx + 2 * cell + 4, by + 6 * cell + 4, 5, WHITE)
    fill_rect(cv, bx + 2 * cell + 1, by + 6 * cell + 6, 7, 5, WHITE)
    fill_circle(cv, bx + 5 * cell + 4, by + 1 * cell + 4, 5, INK)
    fill_rect(cv, bx + 5 * cell + 1, by + 1 * cell + 6, 7, 5, INK)
    # big king silhouette right
    fill_circle(cv, x + 176, y + 30, 14, WHITE)
    fill_rect(cv, x + 164, y + 44, 24, 26, WHITE)
    fill_rect(cv, x + 158, y + 66, 36, 6, WHITE)
    draw_line(cv, x + 176, y + 14, x + 176, y + 8, WHITE, 3)
    draw_line(cv, x + 170, y + 11, x + 182, y + 11, WHITE, 3)
    # "1/2 - 1/2" draw tag
    round_rect(cv, x + 96, y + h - 22, 132, 16, 7, NAVY)
    draw_text(cv, x + 104, y + h - 18, "DRAW  1/2 - 1/2", 1, WHITE)


def ill_blackfriday(cv, x, y, w, h):
    """Black Friday: shopping bags, price tag, rising chart."""
    fill_rect(cv, x, y, w, h, (26, 26, 34))
    # rising chart line
    pts = [(x + 12, y + h - 30), (x + 60, y + h - 44), (x + 110, y + h - 38),
           (x + 160, y + h - 58), (x + 210, y + h - 70)]
    for i in range(len(pts) - 1):
        draw_line(cv, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                  (245, 200, 60), 3)
    draw_line(cv, pts[-1][0], pts[-1][1], pts[-1][0] - 12, pts[-1][1] + 2,
              (245, 200, 60), 3)
    draw_line(cv, pts[-1][0], pts[-1][1], pts[-1][0] - 2, pts[-1][1] + 12,
              (245, 200, 60), 3)
    # shopping bags
    fill_rect(cv, x + 24, y + 30, 52, 44, RED)
    fill_rect(cv, x + 24, y + 30, 52, 8, (170, 40, 30))
    draw_circle_outline(cv, x + 50, y + 32, 8, WHITE, 2)
    fill_rect(cv, x + 92, y + 42, 46, 38, BLUE)
    draw_circle_outline(cv, x + 115, y + 44, 7, WHITE, 2)
    # price tag
    fill_poly(cv, [(x + 158, y + 30), (x + 196, y + 30), (x + 210, y + 44),
                   (x + 196, y + 58), (x + 158, y + 58)], GOLD)
    fill_circle(cv, x + 166, y + 44, 4, (26, 26, 34))
    draw_text(cv, x + 176, y + 38, "$", 2, INK)
    draw_text(cv, x + 176, y + 38, "$", 2, INK)

# ------------------------------------------------------------- card shell
def story_card(cv, x, y, w, h, ill, region, source, status, status_col,
               headline, stat):
    """One illustrated story card: picture top, headline, big stat, chips."""
    round_rect(cv, x, y, w, h, 8, WHITE)
    round_rect_outline(cv, x, y, w, h, 8, (200, 204, 210), 1)
    pic_h = 66
    ill(cv, x + 4, y + 4, w - 8, pic_h)
    # region tag over the picture, top-left
    tw = text_w(region, 1) + 10
    round_rect(cv, x + 8, y + 8, tw, 13, 6, NAVY)
    draw_text(cv, x + 13, y + 11, region, 1, WHITE)
    # headline (2 lines max)
    hy = y + pic_h + 10
    lines = wrap_text(headline, 2, w - 16)[:2]
    for ln in lines:
        draw_text(cv, x + 8, hy, ln, 2, INK)
        hy += 17
    # big stat line
    draw_text(cv, x + 8, y + h - 34, stat, 2, RED)
    # chips row: source + status dot
    cy = y + h - 17
    chip(cv, x + 8, cy, source, WHITE, MIDGREY)
    sx = x + 8 + text_w(source, 1) + 16
    status_dot(cv, sx + 4, cy + 6, status_col)
    draw_text(cv, sx + 11, cy + 3, status, 1, DARKGREY)


# ------------------------------------------------------------- hero panel
def hero(cv, x, y, w, h):
    round_rect(cv, x, y, w, h, 10, NAVY)
    # illustration left
    ill_hero_storm(cv, x + 6, y + 6, 470, h - 12)
    # text right
    tx = x + 492
    chip(cv, tx, y + 14, "USA", WHITE, RED)
    chip(cv, tx + 52, y + 14, "THANKSGIVING", NAVY2, (245, 200, 60))
    draw_text(cv, tx, y + 36, "STORM STOPS", 4, WHITE)
    draw_text(cv, tx, y + 64, "THE PARADE", 4, WHITE)
    draw_text(cv, tx, y + 96, "MACY'S 100TH MARCH POSTPONED FOR THE", 2,
              (200, 210, 225))
    draw_text(cv, tx, y + 113, "FIRST TIME EVER - NOR'EASTER SLAMS", 2,
              (200, 210, 225))
    draw_text(cv, tx, y + 130, "THE EAST COAST", 2, (200, 210, 225))
    # stat blocks
    stats = [("900,000+", "WITHOUT POWER"), ("335+", "FLIGHTS AXED"),
             ("70 MPH", "TOP GUSTS")]
    sx = tx
    for num, lab in stats:
        draw_text(cv, sx, y + 148, num, 3, (245, 200, 60))
        draw_text(cv, sx, y + 170, lab, 1, (200, 210, 225))
        sx += 168
    draw_text(cv, tx, y + h - 16, "SAT 08:30 ET - PARADE MOVES TO SATURDAY",
              1, (160, 175, 195))


# ------------------------------------------------------------- header band
def header(cv):
    fill_rect(cv, 0, 0, W, 86, NAVY)
    fill_rect(cv, 0, 86, W, 4, GOLD)
    draw_text(cv, 14, 12, "THE WORLD IN ONE DAY", 5, WHITE)
    draw_text(cv, 14, 58, "12 STORIES  -  6 CONTINENTS  -  ALL REPORTED TODAY",
              2, (170, 185, 205))
    # date block right
    draw_text(cv, 640, 10, "FRIDAY", 4, (245, 200, 60))
    draw_text(cv, 640, 40, "27 NOVEMBER 2026", 3, WHITE)
    draw_text(cv, 640, 64, "NEWS-IMAGE  -  MAKE.FUN", 1, (170, 185, 205))


# --------------------------------------------------------- timeline strip
TIMELINE = [
    ("07:45", "BANGKOK", "BLAST"),
    ("NIGHT", "GAZA", "STRIKES"),
    ("NIGHT", "UKRAINE", "DRONES"),
    ("15:00", "NEW YORK", "WARNING"),
    ("DAY", "BRUSSELS", "STALLS"),
    ("EVENING", "EAST COAST", "BLACKOUT"),
    ("EVENING", "HORMUZ", "MINED"),
    ("LATE", "CHESS", "DRAW"),
]


def timeline_strip(cv, x, y, w, h):
    round_rect(cv, x, y, w, h, 8, WHITE)
    round_rect_outline(cv, x, y, w, h, 8, (200, 204, 210), 1)
    draw_text(cv, x + 10, y + 8, "THROUGH THE DAY  -  UTC", 2, NAVY)
    legend(cv, x + w - 352, y + 8)
    ly = y + 40
    draw_line(cv, x + 16, ly, x + w - 16, ly, (180, 186, 196), 2)
    cell = (w - 32) / 8.0
    for i, (t, place, what) in enumerate(TIMELINE):
        cx = int(x + 16 + cell * i + cell / 2)
        fill_circle(cv, cx, ly, 6, RED)
        draw_circle_outline(cv, cx, ly, 6, WHITE, 1)
        tw = text_w(t, 1)
        draw_text(cv, cx - tw // 2, y + 24, t, 1, RED)
        pw = text_w(place, 1)
        draw_text(cv, cx - pw // 2, ly + 10, place, 1, INK)
        ww = text_w(what, 1)
        draw_text(cv, cx - ww // 2, ly + 22, what, 1, DARKGREY)


# ------------------------------------------------------ day-in-numbers
NUMBERS = [
    ("900K+", "WITHOUT POWER"),
    ("335+", "FLIGHTS AXED"),
    ("31", "KILLED IN CAIRO"),
    ("9", "HURT IN BANGKOK"),
    ("1.6TN", "EU BUDGET AT STAKE"),
    ("2", "TANKERS MINED"),
    ("$82.5B", "BLACK FRIDAY ONLINE"),
    ("1M", "SATELLITES CLEARED"),
]


def numbers_strip(cv, x, y, w, h):
    round_rect(cv, x, y, w, h, 8, NAVY)
    draw_text(cv, x + 10, y + 8, "THE DAY IN NUMBERS", 2, (245, 200, 60))
    cell = (w - 20) / 8.0
    for i, (num, lab) in enumerate(NUMBERS):
        cx = int(x + 10 + cell * i)
        draw_text(cv, cx + 4, y + 28, num, 3, WHITE)
        lw = text_w(lab, 1)
        # label may wrap to two lines
        lines = wrap_text(lab, 1, int(cell) - 8)
        ly = y + 50
        for ln in lines:
            draw_text(cv, cx + 4, ly, ln, 1, (170, 185, 205))
            ly += 11


# ------------------------------------------------------------- also-on + map
ALSO_ON = [
    ("INDONESIA", "MINE RESCUE: 13 DEAD", "AP"),
    ("NEW ZEALAND", "ELECTION: COALITION 67/131", "RNZ"),
    ("INDIA", "SOORYAVANSHI 204 OFF 53", "BCCI"),
    ("TENNIS", "SINNER OUT OF AUS OPEN", "ATP"),
    ("SPACE", "SPACEX: 1M SATELLITES OK", "FCC"),
    ("TECH", "SAP MAY CUT 10,000 JOBS", "SAP"),
]

# Rough equirectangular world map: continents as flat polygons.
# Coordinates in a 392x76 box below the panel title (lon -180..180 -> x,
# lat 75..-55 -> y).
MAP_BOX = (612, 916, 392, 76)
MAP_DOTS = [
    # (lon, lat, label)
    (-74, 41, "NYC"), (100, 14, "BKK"), (31, 30, "CAIRO"), (34, 31, "GAZA"),
    (31, 50, "KYIV"), (4, 51, "BRUSSELS"), (57, 26, "HORMUZ"),
    (127, 40, "PYONGYANG"), (7, 51, "COLOGNE"), (0, 51, "LONDON"),
    (-58, -35, "BUENOS AIRES"), (77, 13, "INDIA"),
]

CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 68), (-95, 69), (-85, 66),
     (-80, 62), (-75, 58), (-65, 60), (-60, 47), (-70, 42), (-75, 35),
     (-80, 26), (-85, 30), (-90, 29), (-97, 26), (-105, 22), (-110, 24),
     (-115, 30), (-125, 40), (-125, 48), (-135, 58), (-150, 60),
     (-165, 60), (-168, 66)],
    # South America
    [(-80, 10), (-75, 5), (-70, 0), (-60, -5), (-50, -5), (-40, -10),
     (-35, -15), (-40, -25), (-50, -32), (-60, -38), (-70, -40),
     (-73, -50), (-70, -55), (-75, -45), (-80, -30), (-80, -18),
     (-80, -5), (-80, 10)],
    # Europe
    [(-10, 36), (-9, 43), (-2, 48), (0, 50), (5, 53), (8, 57), (10, 59),
     (18, 60), (21, 55), (28, 60), (30, 70), (40, 68), (45, 60), (40, 50),
     (35, 45), (30, 41), (23, 40), (18, 40), (12, 44), (8, 44), (3, 42),
     (0, 38), (-10, 36)],
    # Africa
    [(-17, 15), (-10, 30), (0, 36), (10, 37), (20, 32), (30, 31),
     (35, 28), (40, 15), (43, 11), (48, 10), (51, 2), (45, -5), (40, -15),
     (35, -25), (28, -33), (20, -35), (15, -30), (12, -18), (9, -5),
     (9, 4), (0, 5), (-8, 5), (-17, 15)],
    # Asia
    [(45, 68), (60, 70), (80, 73), (100, 76), (120, 73), (140, 72),
     (160, 70), (178, 66), (170, 60), (160, 55), (142, 50), (140, 40),
     (130, 35), (122, 30), (120, 22), (110, 10), (105, 5), (100, 10),
     (95, 16), (90, 22), (85, 20), (80, 8), (77, 10), (72, 20), (65, 25),
     (58, 26), (52, 28), (48, 30), (44, 39), (40, 42), (42, 46), (40, 55),
     (45, 68)],
    # Australia
    [(114, -22), (122, -14), (132, -12), (142, -11), (146, -19), (150, -23),
     (153, -27), (150, -37), (140, -38), (132, -32), (125, -33), (115, -35),
     (114, -22)],
]


def _map_xy(lon, lat):
    bx, by, bw, bh = MAP_BOX
    mx = bx + int((lon + 180) / 360.0 * bw)
    my = by + int((75 - lat) / 130.0 * bh)
    return mx, my


def world_map(cv, x, y, w, h):
    round_rect(cv, x, y, w, h, 8, (214, 228, 238))
    round_rect_outline(cv, x, y, w, h, 8, (200, 204, 210), 1)
    draw_text(cv, x + 10, y + 6, "WHERE IT HAPPENED", 2, NAVY)
    for poly in CONTINENTS:
        pts = [_map_xy(lon, lat) for lon, lat in poly]
        fill_poly(cv, pts, (120, 150, 130))
    for lon, lat, lab in MAP_DOTS:
        mx, my = _map_xy(lon, lat)
        fill_circle(cv, mx, my, 4, RED)
        draw_circle_outline(cv, mx, my, 4, WHITE, 1)
    # legend of dots
    draw_text(cv, x + 10, y + h - 12, "RED DOT = STORY LOCATION", 1, DARKGREY)


def also_on_band(cv, x, y, w, h):
    round_rect(cv, x, y, w, h, 8, WHITE)
    round_rect_outline(cv, x, y, w, h, 8, (200, 204, 210), 1)
    draw_text(cv, x + 10, y + 8, "ALSO ON 27 NOVEMBER", 2, NAVY)
    cols = 2
    cell_w = (w - 20) // cols
    for i, (region, item, src) in enumerate(ALSO_ON):
        cx = x + 10 + (i % cols) * cell_w
        cy = y + 30 + (i // cols) * 24
        fill_circle(cv, cx + 4, cy + 3, 3, BLUE)
        draw_text(cv, cx + 12, cy, region + ": " + item, 1, INK)
        draw_text(cv, cx + 12, cy + 10, "SOURCE " + src, 1, MIDGREY)


# ------------------------------------------------------------------- footer
def footer(cv):
    fill_rect(cv, 0, 1004, W, 20, NAVY)
    draw_text(cv, 10, 1009, "DATE CHECK: EVERY STORY FIRST REPORTED 27 NOV 2026",
              1, (200, 210, 225))
    draw_text(cv, 560, 1009, "SOURCES: AP - REUTERS - BBC - CNN - WSJ - THE TIMES",
              1, (200, 210, 225))


# -------------------------------------------------------------- legend chips
def legend(cv, x, y):
    draw_text(cv, x, y, "STATUS:", 1, DARKGREY)
    lx = x + 52
    for label, col in (("BREAKING", RED), ("LIVE", TEAL), ("CONFIRMED", GREEN),
                       ("DEVELOPING", AMBER)):
        status_dot(cv, lx + 4, y + 3, col)
        draw_text(cv, lx + 11, y, label, 1, DARKGREY)
        lx += 11 + text_w(label, 1) + 14


# ------------------------------------------------------------------- build
CARDS = [
    (ill_bangkok, "THAILAND", "REUTERS", "BREAKING", RED,
     "BANGKOK REFINERY BLAST", "9 HURT - SHUTDOWN"),
    (ill_cairo, "EGYPT", "BBC", "CONFIRMED", GREEN,
     "CAIRO TANKER FIRE KILLS 31", "31 DEAD - 25 HURT"),
    (ill_gaza, "GAZA", "REUTERS", "LIVE", TEAL,
     "GAZA STRIKES KILL 9", "CEASEFIRE STRAINED"),
    (ill_ukraine, "UKRAINE", "AP", "LIVE", TEAL,
     "KYIV WARNS OF MASS STRIKE", "113 DRONES AT NIGHT"),
    (ill_eu, "EUROPE", "AP", "DEVELOPING", AMBER,
     "EU BUDGET DEADLOCK", "1.6 TN EURO AT RISK"),
    (ill_hormuz, "HORMUZ", "REUTERS", "BREAKING", RED,
     "TWO TANKERS HIT BY MINES", "BLASTS OFF OMAN"),
    (ill_korea, "N. KOREA", "AP", "CONFIRMED", GREEN,
     "KIM VOWS MORE NUKES", "REJECTS TRUMP OFFER"),
    (ill_cologne, "GERMANY", "POLICE", "CONFIRMED", GREEN,
     "COLOGNE BOMB PLOT FOILED", "2 ARRESTED"),
    (ill_uk, "BRITAIN", "ONS", "CONFIRMED", GREEN,
     "NET MIGRATION LOWEST SINCE 1997", "DOWN TO 1997 LEVEL"),
    (ill_argentina, "ARGENTINA", "AP", "DEVELOPING", AMBER,
     "SENATE AXES PRIMARIES", "PRIMARIES SUSPENDED"),
    (ill_chess, "CHESS", "FIDE", "LIVE", TEAL,
     "WORLD TITLE: GAME 3 DRAW", "SCORES STILL LEVEL"),
    (ill_blackfriday, "SHOPPING", "ADOBE", "LIVE", TEAL,
     "BLACK FRIDAY PEAKS TODAY", "$82.5 BN ONLINE"),
]


def build():
    cv = new_canvas(W, H, PAPER)
    header(cv)
    hero(cv, 10, 94, 1004, 200)
    # 12 cards: 3 rows x 4 cols
    cw, ch = 244, 146
    gx, gy = 10, 302
    for i, card in enumerate(CARDS):
        cx = gx + (i % 4) * (cw + 8)
        cy = gy + (i // 4) * (ch + 8)
        story_card(cv, cx, cy, cw, ch, *card)
    timeline_strip(cv, 10, 758, 1004, 66)
    numbers_strip(cv, 10, 830, 1004, 62)
    also_on_band(cv, 10, 898, 592, 100)
    world_map(cv, 610, 898, 404, 100)
    footer(cv)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    path = os.path.join(out_dir, "entry.png")
    size = write_png(cv, path)
    print("wrote %s (%d bytes, %dx%d)" % (path, size, W, H))


if __name__ == "__main__":
    main()
