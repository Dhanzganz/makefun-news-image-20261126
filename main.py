#!/usr/bin/env python3
"""THE WORLD TODAY -- front page for Thursday 26 November 2026.

A pure-stdlib Python program (the grader's Python has no Pillow): it
draws a newspaper front page summing up the day's world news and writes
it as a deterministic 1024x1024 PNG. Everything is drawn by hand --
its own 5x7 bitmap font, its own vector drawing (rectangles, lines,
circles, polygons) and its own PNG encoder (zlib + struct).

Stories on the page:
  LEAD  Hong Kong remembers the 168 lost a year ago -- the one-year
        anniversary of the Wang Fuk Court fire (26 Nov 2025). Survivors
        return to Tai Po on Thursday; the towers stand empty and
        accountability is still open. NOT a new fire.
  SPACE Europe and Japan reach Mercury (BepiColombo, eight-year trip).
  SPACE Pakistan's first astronaut flies (Muhammad Zeeshan Ali,
        Shenzhou-24, bound for Tiangong).
  COURT U.S. convicts Huawei of fraud and trade-secret theft.
  ALSO TODAY: Colombia peace accord 10 years; India Constitution Day
        and Gukesh's chess chase; Senegal rightful AFCON champions
        (CAS); Bangladesh garment wages +36%; China graft probe into
        Shanghai party chief Chen Jining; Flipkart chief to step down.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   -> out/entry.png
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (247, 243, 231)
INK = (18, 18, 18)
RED = (172, 32, 28)
GREY = (96, 92, 82)

# 5x7 bitmap font. Each glyph is 7 rows; each row is a 5-bit mask with
# bit 4 = leftmost pixel. All page text is set in capitals, newspaper
# style, so only capitals, digits and common punctuation are needed.
FONT = {
    "A": (14, 17, 17, 31, 17, 17, 17),
    "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (15, 16, 16, 16, 16, 16, 15),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (15, 16, 16, 23, 17, 17, 14),
    "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (31, 4, 4, 4, 4, 4, 31),
    "J": (7, 2, 2, 2, 2, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13),
    "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30),
    "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 27, 17),
    "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "Z": (31, 1, 2, 4, 8, 16, 31),
    "0": (14, 19, 21, 25, 17, 17, 14),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 2, 4, 8, 31),
    "3": (30, 1, 1, 14, 1, 1, 30),
    "4": (2, 6, 10, 18, 31, 2, 2),
    "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (14, 16, 16, 30, 17, 17, 14),
    "7": (31, 1, 2, 4, 4, 4, 4),
    "8": (14, 17, 17, 14, 17, 17, 14),
    "9": (14, 17, 17, 15, 1, 1, 14),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 12, 12),
    ",": (0, 0, 0, 0, 0, 12, 4),
    ":": (0, 12, 12, 0, 12, 12, 0),
    ";": (0, 12, 12, 0, 12, 12, 4),
    "-": (0, 0, 0, 14, 0, 0, 0),
    "!": (4, 4, 4, 4, 4, 0, 4),
    "?": (14, 17, 1, 2, 4, 0, 4),
    "(": (2, 4, 8, 8, 8, 4, 2),
    ")": (8, 4, 2, 2, 2, 4, 8),
    "/": (1, 1, 2, 4, 8, 16, 16),
    "&": (14, 17, 20, 8, 21, 18, 13),
    "%": (25, 26, 2, 4, 8, 19, 19),
    "+": (0, 4, 4, 14, 4, 4, 0),
    "=": (0, 0, 14, 0, 14, 0, 0),
    '"': (10, 10, 10, 0, 0, 0, 0),
    "'": (4, 4, 8, 0, 0, 0, 0),
    "$": (4, 15, 20, 14, 5, 30, 4),
}


class Canvas:
    """An RGB pixel buffer with small vector-drawing helpers."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        r, g, b = bg
        for i in range(0, len(self.px), 3):
            self.px[i] = r
            self.px[i + 1] = g
            self.px[i + 2] = b

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = c

    def rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        span = (x1 - x0) * 3
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + span] = row

    def hline(self, x0, x1, y, c):
        self.rect(min(x0, x1), y, abs(x1 - x0) + 1, 1, c)

    def vline(self, x, y0, y1, c):
        self.rect(x, min(y0, y1), 1, abs(y1 - y0) + 1, c)

    def line(self, x0, y0, x1, y1, c):
        # Bresenham.
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, c):
        # Filled circle.
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.hline(cx - dx, cx + dx, cy + dy, c)

    def ring(self, cx, cy, r, c):
        # Circle outline.
        steps = max(24, r * 6)
        for i in range(steps):
            a = 2.0 * math.pi * i / steps
            self.set(cx + int(r * math.cos(a)), cy + int(r * math.sin(a)), c)

    def ellipse(self, cx, cy, rx, ry, c):
        # Ellipse outline.
        steps = max(48, (rx + ry) * 3)
        for i in range(steps):
            a = 2.0 * math.pi * i / steps
            self.set(cx + int(rx * math.cos(a)), cy + int(ry * math.sin(a)), c)

    def poly(self, pts, c):
        # Filled polygon (scanline fill over edge intersections).
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    t = (y - y0) / (y1 - y0)
                    xs.append(int(x0 + t * (x1 - x0)))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.hline(xs[j], xs[j + 1], y, c)

    # ---- text ----

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale if s else 0

    def text(self, x, y, s, scale, c, bold=False):
        s = s.upper()
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, c)
            cx += 6 * scale
        if bold:
            self.text(x + 1, y, s, scale, c, bold=False)

    def wrap(self, s, scale, maxw):
        lines = []
        cur = ""
        for word in s.upper().split(" "):
            trial = word if not cur else cur + " " + word
            if self.text_w(trial, scale) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def para(self, x, y, s, scale, maxw, c, lh=None):
        if lh is None:
            lh = 7 * scale + 3
        for line in self.wrap(s, scale, maxw):
            self.text(x, y, line, scale, c)
            y += lh
        return y


# ---- illustrations ----

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def draw_skyline(cv, x, y, w, h):
    """Dusk over Tai Po: gradient sky, tower silhouettes with lit
    windows, dark ground, candle and flower memorial at the foot.
    Every coordinate stays inside the panel (x..x+w, y..y+h)."""
    stops = [
        (0.00, (26, 30, 62)),
        (0.45, (72, 58, 108)),
        (0.75, (176, 92, 72)),
        (1.00, (232, 136, 62)),
    ]
    for row in range(h):
        t = row / max(1, h - 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                cv.hline(x, x + w - 1, y + row, lerp(c0, c1, f))
                break
    # A few early stars in the upper sky.
    stars = [(40, 18), (120, 40), (230, 12), (330, 34), (470, 16),
             (560, 44), (680, 20), (790, 38), (880, 14), (920, 52)]
    for sx, sy in stars:
        cv.set(x + sx, y + sy, (235, 235, 245))
        cv.set(x + sx + 1, y + sy, (200, 200, 220))
    # Towers: (offset, width, height) measured up from the ground line.
    ground = y + h - 56
    towers = [
        (18, 70, 148), (108, 54, 188), (182, 80, 128), (282, 60, 198),
        (362, 90, 158), (472, 56, 208), (548, 84, 138), (652, 62, 182),
        (734, 76, 148), (830, 60, 192),
    ]
    tower_c = (22, 24, 38)
    warm = (255, 214, 120)
    cool = (168, 196, 238)
    for ti, (tx, tw, th) in enumerate(towers):
        cv.rect(x + tx, ground - th, tw, th, tower_c)
        # Rooftop beacon on the two tallest towers.
        if th >= 190:
            cv.set(x + tx + tw // 2, ground - th - 3, (255, 80, 60))
        # Lit windows on a fixed grid; all inside the tower rect.
        cols = tw // 13
        rows = th // 17
        for r in range(rows):
            for cc in range(cols):
                if (r * 3 + cc * 5 + ti) % 4 == 0:
                    continue
                wx = x + tx + 6 + cc * 13
                wy = ground - th + 8 + r * 17
                cv.rect(wx, wy, 4, 6, warm if (r + cc) % 3 else cool)
    # Dark ground band.
    cv.rect(x, ground, w, h - (ground - y), (14, 16, 26))
    # Memorial: three candles with flames, ringed by small flowers.
    base = y + h - 8
    for i, cx in enumerate((x + 610, x + 640, x + 670)):
        cv.rect(cx - 3, base - 22, 7, 22, (240, 236, 224))
        cv.disc(cx, base - 27, 4, (255, 170, 60))
        cv.disc(cx, base - 27, 2, (255, 230, 140))
    flowers = [(x + 590, base - 6, (224, 122, 152)),
               (x + 600, base - 2, (240, 240, 235)),
               (x + 660, base - 4, (240, 200, 90)),
               (x + 690, base - 8, (224, 122, 152)),
               (x + 700, base - 3, (240, 240, 235)),
               (x + 580, base - 10, (240, 200, 90))]
    for fx, fy, fc in flowers:
        cv.disc(fx, fy, 3, fc)


def draw_mercury(cv, x, y, w, h):
    """Mercury with its orbit ring and a small spacecraft. The orbit
    ellipse is drawn first and the planet disc on top, so no part of
    the orbit band ever crosses the planet."""
    cv.rect(x, y, w, h, (14, 16, 32))
    for sx, sy in [(14, 12), (40, 30), (260, 16), (280, 44), (90, 90),
                   (210, 96), (150, 8), (30, 70)]:
        cv.set(x + sx, y + sy, (220, 220, 235))
    cx, cy = x + w // 2, y + h // 2
    cv.ellipse(cx, cy, w // 2 - 12, h // 2 - 16, (196, 200, 212))
    cv.disc(cx, cy, 30, (178, 142, 112))
    for dx, dy, r in [(-12, -8, 5), (8, 6, 4), (-4, 12, 3), (14, -12, 3),
                      (2, -2, 2), (-16, 8, 2)]:
        cv.disc(cx + dx, cy + dy, r, (140, 106, 80))
    # Spacecraft riding the orbit, upper right.
    sx = cx + int((w // 2 - 12) * 0.72)
    sy = cy - int((h // 2 - 16) * 0.68)
    cv.rect(sx - 5, sy - 3, 10, 6, (235, 235, 240))
    cv.rect(sx - 14, sy - 1, 9, 2, (120, 160, 220))
    cv.rect(sx + 5, sy - 1, 9, 2, (120, 160, 220))


def draw_rocket(cv, x, y, w, h):
    """Rocket climbing past the Tiangong station."""
    cv.rect(x, y, w, h, (18, 30, 58))
    cv.rect(x, y + h - 26, w, 26, (34, 52, 92))
    for sx, sy in [(16, 14), (52, 34), (240, 12), (272, 40), (150, 10),
                   (200, 60), (90, 70)]:
        cv.set(x + sx, y + sy, (225, 225, 240))
    # Rocket, left of centre, nose up.
    rx = x + 62
    cv.rect(rx, y + 30, 18, 52, (238, 238, 240))
    cv.poly([(rx, y + 30), (rx + 18, y + 30), (rx + 9, y + 12)], (198, 40, 36))
    cv.poly([(rx, y + 82), (rx - 10, y + 96), (rx, y + 82)], (198, 40, 36))
    cv.poly([(rx + 18, y + 82), (rx + 28, y + 96), (rx + 18, y + 82)],
            (198, 40, 36))
    cv.disc(rx + 9, y + 48, 5, (40, 90, 160))
    cv.poly([(rx + 3, y + 82), (rx + 15, y + 82), (rx + 9, y + 104)],
            (255, 170, 60))
    # Station, right: core bar, solar panels, module.
    cv.rect(x + 168, y + 34, 112, 9, (200, 204, 210))
    cv.rect(x + 168, y + 24, 34, 6, (70, 110, 190))
    cv.rect(x + 246, y + 24, 34, 6, (70, 110, 190))
    cv.rect(x + 168, y + 43, 34, 6, (70, 110, 190))
    cv.rect(x + 246, y + 43, 34, 6, (70, 110, 190))
    cv.disc(x + 224, y + 38, 8, (160, 164, 172))
    cv.rect(x + 216, y + 46, 16, 10, (140, 144, 152))


def draw_scales(cv, x, y, w, h):
    """Scales of justice beside a rising bar chart."""
    cv.rect(x, y, w, h, (238, 232, 218))
    cx = x + 88
    cv.vline(cx, y + 14, y + 86, INK)
    cv.hline(cx - 42, cx + 42, y + 22, INK)
    cv.disc(cx, y + 16, 4, INK)
    for side in (-1, 1):
        px = cx + side * 42
        cv.line(px, y + 22, px - 12, y + 52, INK)
        cv.line(px, y + 22, px + 12, y + 52, INK)
        cv.poly([(px - 14, y + 52), (px + 14, y + 52), (px, y + 66)],
                (120, 96, 60))
    cv.hline(cx - 30, cx + 30, y + 90, INK)
    # Bars, rising left to right.
    base = y + 92
    for i, bh in enumerate((26, 44, 62)):
        bx = x + 178 + i * 36
        cv.rect(bx, base - bh, 24, bh, (52, 74, 108))
    cv.hline(x + 168, x + 292, base, INK)


# ---- page layout ----

M = 36            # page margin
CW = W - 2 * M    # content width: 952


def build():
    cv = Canvas(W, H, PAPER)

    # Masthead.
    cv.rect(M, 38, CW, 3, INK)
    title = "THE WORLD TODAY"
    cv.text((W - cv.text_w(title, 6)) // 2, 52, title, 6, INK, bold=True)
    cv.rect(M, 102, CW, 2, INK)
    date = "THURSDAY 26 NOVEMBER 2026"
    cv.text((W - cv.text_w(date, 2)) // 2, 110, date, 2, INK)
    cv.rect(M, 132, CW, 3, INK)

    # Lead story.
    cv.text(M, 146, "HONG KONG: ONE YEAR ON", 2, RED, bold=True)
    cv.text(M, 168, "HONG KONG REMEMBERS THE 168 LOST A YEAR AGO",
            3, INK, bold=True)
    lead_body = (
        "SURVIVORS AND BEREAVED FAMILIES RETURN TO WANG FUK COURT IN "
        "TAI PO ON THURSDAY, A YEAR AFTER THE FIRE THAT KILLED 168 "
        "PEOPLE. THE TOWERS STAND EMPTY AND NEARLY 2,000 FAMILIES REMAIN "
        "DISPLACED, WHILE FAMILIES ASK WHO WILL BE HELD TO ACCOUNT.")
    cv.para(M, 200, lead_body, 2, CW, INK)
    draw_skyline(cv, M, 280, CW, 276)
    cv.text(M, 564,
            "DUSK OVER TAI PO: THE WANG FUK COURT TOWERS STAND EMPTY A "
            "YEAR AFTER THE FIRE THAT KILLED 168 PEOPLE.",
            1, GREY)
    cv.rect(M, 588, CW, 2, INK)

    # Three secondary stories in a row.
    cols = [
        ("SPACE", "EUROPE AND JAPAN REACH MERCURY",
         "BEPI COLOMBO ENDS ITS EIGHT-YEAR JOURNEY AND SLIPS INTO ORBIT "
         "AROUND THE SMALLEST PLANET.",
         draw_mercury),
        ("SPACE", "PAKISTAN'S FIRST ASTRONAUT FLIES",
         "MUHAMMAD ZEESHAN ALI JOINS CHINA'S SHENZHOU-24, THE FIRST "
         "FOREIGN ASTRONAUT BOUND FOR TIANGONG.",
         draw_rocket),
        ("COURTS", "U.S. CONVICTS HUAWEI OF FRAUD",
         "A U.S. JURY FINDS HUAWEI GUILTY OF FRAUD AND TRADE-SECRET "
         "THEFT; NEW TARIFFS ARE READIED.",
         draw_scales),
    ]
    col_w = 301
    for i, (kicker, head, body, draw) in enumerate(cols):
        cx = M + i * (col_w + 24)
        cv.text(cx, 602, kicker, 1, RED, bold=True)
        cv.para(cx, 614, head, 2, col_w, INK, lh=18)
        draw(cv, cx, 658, col_w, 114)
        cv.para(cx, 782, body, 1, col_w, INK, lh=11)
    cv.rect(M, 838, CW, 2, INK)

    # Also today strip.
    cv.text(M, 850, "ALSO TODAY", 2, RED, bold=True)
    items = [
        "COLOMBIA MARKS 10 YEARS SINCE ITS PEACE ACCORD",
        "INDIA CELEBRATES CONSTITUTION DAY AS GUKESH CHASES THE WORLD CHESS CROWN",
        "SENEGAL DECLARED RIGHTFUL AFCON CHAMPIONS BY CAS",
        "BANGLADESH RAISES GARMENT WAGES BY 36 PERCENT",
        "CHINA OPENS GRAFT PROBE INTO SHANGHAI PARTY CHIEF CHEN JINING",
        "FLIPKART CHIEF KALYAN KRISHNAMURTHY TO STEP DOWN",
    ]
    for i, item in enumerate(items):
        ix = M + (i % 2) * 482
        iy = 878 + (i // 2) * 24
        cv.rect(ix, iy + 1, 5, 5, RED)
        cv.text(ix + 11, iy, item, 1, INK)

    # Footer rule and line; the layout bottom is y=968.
    cv.rect(M, 946, CW, 2, INK)
    foot = "THE WORLD TODAY - THURSDAY 26 NOVEMBER 2026 - PAGE 1"
    cv.text((W - cv.text_w(foot, 1)) // 2, 954, foot, 1, GREY)
    return cv


# ---- PNG encoder (own, stdlib only) ----

def _chunk(tag, data):
    out = struct.pack(">I", len(data)) + tag + data
    out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw += cv.px[y * W * 3:(y + 1) * W * 3]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    write_png(cv, os.path.join(outdir, "entry.png"))


if __name__ == "__main__":
    main()
