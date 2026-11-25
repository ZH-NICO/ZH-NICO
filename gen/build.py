"""Generates every SVG in ../assets. Run: python gen/build.py"""
import math
import os

from f40 import frames, ROWS

OUT = os.path.join(os.path.dirname(__file__), "..", "assets")
FONT = "'JetBrains Mono','Fira Code','Cascadia Code',Consolas,'DejaVu Sans Mono','Courier New',monospace"
RED, HOT, GOLD, INK, DIM, BG = "#ff2800", "#ff6a3d", "#ffd200", "#f2efe9", "#6b6b73", "#07070a"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg(w, h, body, title):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="{FONT}" role="img"><title>{esc(title)}</title>{body}</svg>\n')


def text(x, y, s, size=12, fill=INK, extra="", pitch=None):
    """Monospace text; with pitch, textLength pins every glyph to an exact column grid across fonts."""
    tl = f' textLength="{len(s) * pitch:.1f}" lengthAdjust="spacingAndGlyphs"' if pitch and s.strip() else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" xml:space="preserve"{tl} {extra}>{esc(s)}</text>'


def common_defs():
    return f'''<defs>
<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".45"/></pattern>
<radialGradient id="vig" cx="50%" cy="50%" r="75%"><stop offset="60%" stop-color="#000" stop-opacity="0"/><stop offset="100%" stop-color="#000" stop-opacity=".85"/></radialGradient>
<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="glow2" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>'''


def frame_overlay(w, h):
    return (f'<rect width="{w}" height="{h}" fill="url(#scan)" class="flick"/>'
            f'<rect width="{w}" height="{h}" fill="url(#vig)"/>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="none" stroke="{RED}" stroke-opacity=".35"/>')


BASE_CSS = """
.flick{animation:flick 3.7s infinite}
@keyframes flick{0%,100%{opacity:1}47%{opacity:1}48%{opacity:.55}49%{opacity:1}83%{opacity:.8}84%{opacity:1}}
.blink{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}
"""


def typed(x, y, s, begin, size=13, fill=INK, cps=28, pitch=None):
    """Typewriter reveal: a clip rect grows one character width at a time."""
    pitch = pitch or size * 0.6
    w = len(s) * pitch
    dur = max(len(s) / cps, 0.05)
    cid = f"t{abs(hash((x, y, s))) % 10**8}"
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y - size}" height="{size * 1.5}" width="0">'
            f'<animate attributeName="width" from="0" to="{w + 2:.1f}" begin="{begin:.2f}s" dur="{dur:.2f}s" '
            f'calcMode="discrete" values="{";".join(f"{i * pitch:.1f}" for i in range(len(s) + 2))}" fill="freeze"/></rect></clipPath>'
            f'<g clip-path="url(#{cid})">{text(x, y, s, size, fill, pitch=pitch)}</g>')


# ---------------------------------------------------------------- hero

def hero(fr):
    W, H = 1000, 560
    n, period = len(fr), 7.2
    cx0, cy0, px, py = 14, 152, 6.6, 11  # car grid origin, column pitch, row pitch
    slot = 100 / n
    css = BASE_CSS + f"""
.fr{{visibility:hidden;animation:spin {period}s infinite}}
@keyframes spin{{0%{{visibility:visible}}{slot:.4f}%{{visibility:hidden}}100%{{visibility:hidden}}}}
.draw{{fill:transparent;stroke:{RED};stroke-width:1.2;stroke-dasharray:420;stroke-dashoffset:420;animation:draw 2.6s .2s ease-out forwards}}
@keyframes draw{{70%{{stroke-dashoffset:0;fill:transparent}}100%{{stroke-dashoffset:0;fill:{INK}}}}}
.gl{{animation:gl 4.3s infinite steps(1)}}
@keyframes gl{{0%,100%{{transform:translate(0,0);opacity:0}}61%{{transform:translate(-4px,0);opacity:.9}}62%{{transform:translate(5px,1px);opacity:.9}}63%{{opacity:0}}88%{{transform:translate(3px,-1px);opacity:.8}}89%{{opacity:0}}}}
.lines text{{animation:zoom 1.1s linear infinite}}
@keyframes zoom{{from{{transform:translateX(0)}}to{{transform:translateX(-240px)}}}}
"""
    b = [f"<style>{css}</style>", common_defs(),
         f'''<defs><linearGradient id="paint" gradientUnits="userSpaceOnUse" x1="0" y1="{cy0 + 40}" x2="0" y2="{cy0 + ROWS * py - 40}">
<stop offset="0" stop-color="#ffe0d0"/><stop offset=".3" stop-color="{HOT}"/><stop offset=".6" stop-color="{RED}"/><stop offset="1" stop-color="#7a0b00"/></linearGradient>
<radialGradient id="floor" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{RED}" stop-opacity=".35"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></radialGradient>
<path id="ring" d="M 46 462 a 330 56 0 1 0 660 0 a 330 56 0 1 0 -660 0 a 330 56 0 1 0 660 0 a 330 56 0 1 0 -660 0"/></defs>''',
         f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>',
         f'<ellipse cx="376" cy="462" rx="420" ry="110" fill="url(#floor)"/>']

    # speed streaks in the background (text dashes scrolling)
    b.append('<g class="lines" opacity=".22">')
    for i, y in enumerate(range(176, 540, 26)):
        s = ("━━━━  ─ ─   ━━   ─────   ━  " * 9)[(i * 7) % 11:]
        b.append(f'<g style="animation-delay:-{i * .13:.2f}s">{text(-10, y, s, 9, RED if i % 3 else GOLD, f"style=\"animation-delay:-{i * .29:.2f}s;animation-duration:{.7 + (i % 4) * .25:.2f}s\"")}</g>')
    b.append("</g>")

    # turntable ring: characters marching around an ellipse
    circ = 2 * math.pi * math.sqrt((330 ** 2 + 56 ** 2) / 2)
    ring = ("─ · " * 200)[:int(circ / 7.2)]
    b.append(f'<text font-size="12" fill="{RED}" opacity=".55" filter="url(#glow)" textLength="{circ:.0f}" lengthAdjust="spacingAndGlyphs">'
             f'<textPath href="#ring" startOffset="0">{esc(ring)}<animate attributeName="startOffset" from="0" to="{circ:.0f}" dur="{period}s" repeatCount="indefinite"/></textPath></text>')

    # the car: n pre-rendered frames, one visible at a time
    layers = [(" .,-~", "#8f1400"), (":;=!", RED), ("*#", HOT), ("$@", "#ffe3d6")]
    b.append('<g filter="url(#glow)" font-size="11.4">')
    for i, rows in enumerate(fr):
        g = [f'<g class="fr" style="animation-delay:{i * period / n:.3f}s">']
        for chars, col in layers:
            g.append(f'<g fill="{col}">')
            for r, row in enumerate(rows):
                t = "".join(ch if ch in chars and ch != " " else " " for ch in row).rstrip()
                if t:
                    lead = len(t) - len(t.lstrip())
                    t = t.lstrip()
                    g.append(f'<text x="{cx0 + lead * px:.1f}" y="{cy0 + r * py}" xml:space="preserve" textLength="{len(t) * px:.1f}" lengthAdjust="spacingAndGlyphs">{esc(t)}</text>')
            g.append("</g>")
        g.append("</g>")
        b.append("".join(g))
    b.append("</g>")

    # header bar
    b.append(text(26, 34, "● ● ●", 12, RED) + text(80, 34, "zh-nico@maranello:~/garage", 12, DIM))
    b.append(typed(300, 34, "$ ./ignite --model F40 --colour rosso-corsa", .2, 12, INK))
    b.append(f'<line x1="20" y1="48" x2="{W - 20}" y2="48" stroke="{RED}" stroke-opacity=".3" stroke-dasharray="2 4"/>')

    # title: stroke-drawn then filled, with a glitch ghost
    b.append(f'<g font-size="60" font-weight="700" letter-spacing="6">'
             f'<text x="36" y="118" class="gl" fill="{GOLD}" opacity="0">ZH-NICO</text>'
             f'<text x="36" y="118" class="draw" filter="url(#glow)">ZH-NICO</text></g>')
    b.append(typed(40, 142, "Informatiker · Applikationsentwickler · Schweiz", 2.4, 13, HOT))

    # HUD spec sheet
    hx, hy = 686, 92
    spec = [("MODEL", "F40 · 1987"), ("ENGINE", "2.9 L V8 twin-turbo"), ("POWER", "478 PS @ 7000 rpm"),
            ("TORQUE", "577 Nm @ 4000 rpm"), ("V-MAX", "324 km/h"), ("WEIGHT", "1100 kg dry"),
            ("DRIVER", "ZH-NICO"), ("STATUS", "pushing commits")]
    b.append(text(hx, hy, "┌─ SPEC SHEET ────────────────────┐", 12, RED, pitch=7.2))
    for i, (k, v) in enumerate(spec):
        y = hy + 22 + i * 21
        b.append(text(hx, y, "│", 12, RED, pitch=7.2) + text(hx + 7.2 * 33, y, "│", 12, RED, pitch=7.2))
        b.append(text(hx + 14, y, k, 11, DIM))
        b.append(typed(hx + 74, y, v, 1.0 + i * .45, 12, GOLD if k == "DRIVER" else INK, pitch=7.2))
    yb = hy + 22 + len(spec) * 21 - 6
    b.append(text(hx, yb, "└─────────────────────────────────┘", 12, RED, pitch=7.2))
    b.append(text(hx + 6, yb + 26, "RPM", 10, DIM))
    # live rev bar under the spec sheet
    for i in range(18):
        c = "#30d158" if i < 9 else GOLD if i < 14 else RED
        b.append(f'<g opacity=".15">{text(hx + 36 + i * 9.6, yb + 27, "▮", 13, c)}'
                 f'<animate attributeName="opacity" values=".15;.15;1;1;.15" keyTimes="0;{i / 30:.3f};{i / 30 + .02:.3f};.7;1" dur="1.6s" repeatCount="indefinite"/></g>')
    b.append(text(hx + 6, yb + 54, "LAP", 10, DIM) + text(hx + 36, yb + 54, "1:27.4", 13, INK) +
             text(hx + 112, yb + 54, "Δ -0.38", 13, "#30d158") + text(hx + 182, yb + 54, "█", 13, RED, 'class="blink"'))

    b.append(text(26, H - 16, "▲ 360° live ascii render · 60 frames · pure svg", 10, DIM))
    b.append(text(W - 236, H - 16, "ROSSO CORSA  #FF2800", 10, RED))
    b.append(frame_overlay(W, H))
    return svg(W, H, "".join(b), "ZH-NICO — rotating ASCII F40")


# ---------------------------------------------------------------- telemetry (tach + driver card)

REV = [(0, 950), (.8, 1000), (1.6, 7800), (1.75, 5200), (3.0, 7850), (3.15, 5600), (4.3, 7900),
       (4.45, 7600), (4.6, 7900), (4.75, 7600), (4.9, 7900), (6.6, 1000), (8.0, 950)]
SHIFTS = [(0, "N"), (.8, "1"), (1.75, "2"), (3.15, "3"), (6.6, "N")]


def rpm_at(t):
    for (t0, r0), (t1, r1) in zip(REV, REV[1:]):
        if t0 <= t <= t1:
            return r0 + (r1 - r0) * (t - t0) / (t1 - t0)
    return REV[-1][1]


def gear_at(t):
    return [g for t0, g in SHIFTS if t >= t0][-1]


def telemetry():
    W, H, T = 1000, 300, 8.0
    cx, cy, R = 160, 160, 112
    ang = lambda rpm: 135 + 270 * rpm / 8000
    b = [f"<style>{BASE_CSS}</style>", common_defs(), f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>']
    # dial ticks + numerals, all monospace glyphs placed on the arc
    for k in range(0, 33):
        rpm = k * 250
        a = math.radians(ang(rpm))
        major = k % 4 == 0
        c = RED if rpm >= 7000 else INK if major else DIM
        x, y = cx + R * math.cos(a), cy + R * math.sin(a)
        b.append(text(f"{x:.1f}", f"{y:.1f}", "█" if major else "▏", 12 if major else 10, c,
                      f'text-anchor="middle" dominant-baseline="central" transform="rotate({ang(rpm) + 90:.1f} {x:.1f} {y:.1f})"'))
        if major:
            xn, yn = cx + (R - 24) * math.cos(a), cy + (R - 24) * math.sin(a)
            b.append(text(f"{xn:.1f}", f"{yn:.1f}", str(rpm // 1000), 15, c, 'text-anchor="middle" dominant-baseline="central" font-weight="700"'))
    b.append(text(cx, cy + 42, "x1000 r/min", 9, DIM, 'text-anchor="middle"'))
    # needle
    kt = ";".join(f"{t / T:.4f}" for t, _ in REV)
    vals = ";".join(f"{ang(r):.1f} {cx} {cy}" for _, r in REV)
    b.append(f'<g filter="url(#glow)">{text(cx, cy, "  ━━━━━━━━━━━▶", 13, RED, "dominant-baseline=\"central\"")}'
             f'<animateTransform attributeName="transform" type="rotate" values="{vals}" keyTimes="{kt}" dur="{T}s" repeatCount="indefinite"/></g>')
    b.append(text(cx, cy, "◉", 22, INK, 'text-anchor="middle" dominant-baseline="central"'))

    # sampled discrete readouts: gear, speed, shift lights
    steps = [i * 0.1 for i in range(int(T * 10))]
    ktd = ";".join(f"{t / T:.4f}" for t in steps)
    ratio = {"N": 0, "1": 9.6, "2": 15.8, "3": 41.0}
    speeds = [min(int(rpm_at(t) / 1000 * ratio[gear_at(t)]), 324) for t in steps]
    # gear digit
    gx, gy = cx, cy + 74
    b.append(text(gx - 54, gy - 12, "GEAR", 9, DIM))
    for g in "N123":
        v = ";".join("1" if gear_at(t) == g else "0" for t in steps)
        b.append(f'<g opacity="0">{text(gx, gy, g, 34, GOLD if g != "N" else "#30d158", "text-anchor=\"middle\" font-weight=\"700\" filter=\"url(#glow)\"")}'
                 f'<animate attributeName="opacity" values="{v}" keyTimes="{ktd}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></g>')

    # odometer-roll speed digits
    sx, sy = 330, 92
    b.append(text(sx, sy - 40, "SPEED", 10, DIM) + text(sx + 150, sy, "km/h", 12, DIM))
    b.append(f'<clipPath id="odo"><rect x="{sx - 4}" y="{sy - 44}" width="140" height="54"/></clipPath><g clip-path="url(#odo)">')
    for d in range(3):
        col = "".join(f'<text x="{sx + d * 44}" y="{sy + i * 54}" font-size="54" font-weight="700" fill="{INK}">{i}</text>' for i in range(10))
        div = 10 ** (2 - d)
        v = ";".join(f"0 {-54 * ((s // div) % 10)}" for s in speeds)
        b.append(f'<g>{col}<animateTransform attributeName="transform" type="translate" values="{v}" keyTimes="{ktd}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></g>')
    b.append("</g>")
    # shift lights
    for i in range(12):
        thr = 4600 + i * 270
        c = "#30d158" if i < 5 else GOLD if i < 9 else RED
        v = ";".join("1" if rpm_at(t) >= thr and not (rpm_at(t) > 7700 and int(t * 10) % 2) else ".12" for t in steps)
        b.append(f'<g opacity=".12">{text(sx + i * 17, sy + 36, "●", 16, c, "filter=\"url(#glow)\"")}'
                 f'<animate attributeName="opacity" values="{v}" keyTimes="{ktd}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></g>')
    b.append(text(sx, sy + 70, "TURBO", 10, DIM))
    for i in range(14):
        b.append(f'<g opacity=".15">{text(sx + 46 + i * 9.4, sy + 70, "▰", 12, HOT)}'
                 f'<animate attributeName="opacity" values="{";".join("1" if rpm_at(t) > 3000 + i * 330 else ".15" for t in steps)}" keyTimes="{ktd}" calcMode="discrete" dur="{T}s" repeatCount="indefinite"/></g>')
    b.append(text(sx, sy + 100, "BOOST 1.1 bar   OIL 98°C   H2O 86°C", 10, DIM))
    b.append(text(sx, sy + 124, "TC OFF   ABS n/a   VIBES MAX", 10, RED))

    # driver card
    px0, py0, P = 560, 46, 7.4
    card = [("NAME", "Nico Schult"), ("HANDLE", "@ZH-NICO"), ("BASE", "ZH · Schweiz"),
            ("ROLE", "Informatiker Applikationsentwicklung"), ("BUILDING", "ultraclaude · neon-strike"),
            ("STACK", "JS · TS · Java · Docker"), ("FUEL", "espresso + clean commits")]
    b.append(text(px0, py0, "╔═ DRIVER TELEMETRY ═══════════════════════════════╗", 12, RED, pitch=P))
    for i, (k, v) in enumerate(card):
        y = py0 + 28 + i * 27
        b.append(text(px0, y, "║", 12, RED, pitch=P) + text(px0 + 51 * P, y, "║", 12, RED, pitch=P))
        b.append(text(px0 + 16, y, k, 10, DIM))
        b.append(typed(px0 + 96, y, v, .4 + i * .55, 12, GOLD if k == "HANDLE" else INK, pitch=P))
    yb = py0 + 28 + len(card) * 27 - 8
    b.append(text(px0, yb, "╚══════════════════════════════════════════════════╝", 12, RED, pitch=P))
    b.append(text(px0 + 8, yb + 28, ">", 12, RED) + typed(px0 + 22, yb + 28, "telemetry stream ok — buckle up", 4.6, 12, DIM, pitch=P)
             + text(px0 + 22 + 31 * P + 4, yb + 28, "▌", 12, RED, 'class="blink"'))
    b.append(frame_overlay(W, H))
    return svg(W, H, "".join(b), "Driver telemetry — tachometer and profile")


# ---------------------------------------------------------------- gearbox (tech stack)

GEARS = [("1", "JAVASCRIPT", "neon-strike · ultraclaude", "#f7df1e"), ("2", "TYPESCRIPT", "uek335-movies · minishop UI", "#3178c6"),
         ("3", "JAVA", "minishop backend", "#f89820"), ("4", "HTML / CSS", "web & layouts", "#e34f26"),
         ("5", "NODE.JS", "websockets · servers", "#5fa04e"), ("6", "DOCKER", "containers everywhere", "#2496ed"),
         ("R", "GIT", "rewind · rebase · retry", "#f05032")]


def gearbox():
    W, H, T = 1000, 270, 10.5
    gx, gy, sp = 90, 70, 110  # gate origin and spacing
    pos = {"1": (0, 0), "2": (0, 2), "3": (1, 0), "4": (1, 2), "5": (2, 0), "6": (2, 2), "R": (3, 0)}
    xy = lambda g: (gx + pos[g][0] * sp, gy + pos[g][1] * 60)
    b = [f"<style>{BASE_CSS}</style>", common_defs(), f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>']
    b.append(text(26, 34, "GEARBOX // TECH STACK", 12, RED, 'letter-spacing="2"') + text(250, 34, "6-speed manual · gated · no paddles", 11, DIM))
    # gate drawn with box-drawing glyphs on an exact grid
    P, L = 7.2, 14
    cols = int(3 * sp / P) + 1
    mid = gy + 60
    b.append(f'<g fill="{DIM}" font-size="13">')
    b.append(text(gx, mid + 4, "═" * cols, 13, DIM, pitch=P))
    for c in range(4):
        x = gx + c * sp
        rng = (0, 1) if c == 3 else (0, 2)
        for yy in range(gy, gy + 60 * rng[1] + 1, L):
            b.append(text(x - P / 2, yy + 4, "║", 13, DIM, pitch=P))
    b.append("</g>")
    for g in pos:
        x, y = xy(g)
        b.append(text(x, y - 14 if pos[g][1] == 0 else y + 28, g, 16, INK, 'text-anchor="middle" font-weight="700"'))
    # knob path through the gates
    seq = ["N", "1", "2", "3", "4", "5", "6", "N", "R", "N"]
    pts, kts, tt = [], [], 0.0
    def at(g):
        return (gx + sp, mid) if g == "N" else xy(g)
    prev = None
    keypts = []
    for g in seq:
        p = at(g)
        if prev is not None:
            # route via the neutral rail: up/down to rail, across, then into gate
            for q in ((prev[0], mid), (p[0], mid), p):
                if q != pts[-1]:
                    pts.append(q)
        else:
            pts.append(p)
        keypts.append(len(pts) - 1)
        prev = p
    # dwell timing: each gear holds, transitions are quick
    n = len(pts)
    times = []
    dwell, move = 0.9, 0.12
    t = 0.0
    for i in range(n):
        times.append(t)
        t += dwell if i in keypts else move
    total = t
    path = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    kt = ";".join(f"{x / total:.4f}" for x in times)
    vals = ";".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    b.append(f'<g filter="url(#glow2)">{text(0, 0, "◉", 26, RED, "text-anchor=\"middle\" dominant-baseline=\"central\"")}'
             f'<animateTransform attributeName="transform" type="translate" values="{vals};{vals.split(";")[0]}" keyTimes="{kt};1" dur="{total:.2f}s" repeatCount="indefinite"/></g>')
    # right panel: which gear is engaged
    rx, ry = 520, 78
    b.append(text(rx, ry - 20, "ENGAGED", 10, DIM))
    dwell_windows = []
    for k, idx in enumerate(keypts):
        g = seq[k]
        t0 = times[idx]
        t1 = times[idx] + dwell
        dwell_windows.append((g, t0 / total, t1 / total))
    for code, name, note, col in GEARS:
        wins = [(a, z) for g, a, z in dwell_windows if g == code]
        if not wins:
            continue
        a, z = wins[0]
        op = f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{a:.4f};{z:.4f}" calcMode="discrete" dur="{total:.2f}s" repeatCount="indefinite"/>'
        b.append(f'<g opacity="0">{text(rx, ry + 34, code, 64, col, "font-weight=\"700\" filter=\"url(#glow)\"")}'
                 f'{text(rx + 62, ry + 6, name, 26, INK, "font-weight=\"700\" letter-spacing=\"3\"")}'
                 f'{text(rx + 64, ry + 34, "└─ " + note, 12, DIM)}{op}</g>')
    b.append(f'<g opacity="0">{text(rx, ry + 34, "N", 64, "#30d158", "font-weight=\"700\" filter=\"url(#glow)\"")}'
             f'{text(rx + 62, ry + 6, "NEUTRAL", 26, DIM, "letter-spacing=\"3\"")}'
             f'<animate attributeName="opacity" values="{";".join("1" if g == "N" else "0" for g, _, _ in dwell_windows)};0" '
             f'keyTimes="{";".join(f"{a:.4f}" for _, a, _ in dwell_windows)};1" calcMode="discrete" dur="{total:.2f}s" repeatCount="indefinite"/></g>')
    # legend strip
    for i, (code, name, _, col) in enumerate(GEARS):
        x = 520 + (i % 4) * 118
        y = 186 + (i // 4) * 26
        b.append(text(x, y, f"[{code}]", 11, col) + text(x + 30, y, name.title() if name != "HTML / CSS" else "HTML/CSS", 11, INK))
    b.append(text(26, H - 18, "◉ knob runs the gate on a loop  ·  ratios tuned for shipping", 10, DIM))
    b.append(frame_overlay(W, H))
    return svg(W, H, "".join(b), "Tech stack as a gated gearbox")


# ---------------------------------------------------------------- project cards

PROJECTS = [("01", "ultraclaude", ["Run a team of Claude Code agents in one", "window: roles, shared memory, messaging", "and a live overview."], "JavaScript", "#f7df1e"),
            ("02", "neon-strike", ["2D online arena shooter.", "Node + WebSockets, server-authoritative", "netcode."], "JavaScript", "#f7df1e"),
            ("03", "uek335-movies", ["Movie app in TypeScript,", "built for ÜK 335."], "TypeScript", "#3178c6"),
            ("04", "minishop", ["Full-stack mini shop: Java backend,", "TypeScript frontend, dockerised."], "Java · TS", "#f89820")]


def card(no, name, desc, lang, col, k):
    W, H = 490, 176
    b = [f"<style>{BASE_CSS}.sw{{animation:sw 2.4s linear infinite}}@keyframes sw{{from{{transform:translateX(-500px)}}to{{transform:translateX(500px)}}}}</style>",
         common_defs(), f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>',
         f'<linearGradient id="sh"><stop offset="0" stop-color="{RED}" stop-opacity="0"/><stop offset=".5" stop-color="{RED}" stop-opacity=".18"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></linearGradient>',
         f'<rect class="sw" width="160" height="{H}" fill="url(#sh)" style="animation-delay:{k * .6:.1f}s"/>']
    b.append(text(22, 32, f"PIT {no}", 11, RED, 'letter-spacing="2"') + text(84, 32, "─" * 40, 11, RED, 'opacity=".4"', pitch=6.6))
    b.append(f'<g filter="url(#glow)">{typed(22, 66, name, .2 + k * .3, 24, INK, cps=18, pitch=14.4)}</g>')
    for i, line in enumerate(desc):
        b.append(text(22, 96 + i * 18, line, 12, "#b9b6b0"))
    b.append(text(22, H - 18, "●", 12, col) + text(38, H - 18, lang, 11, DIM))
    # lap timer strip
    for i in range(16):
        b.append(f'<g opacity=".2">{text(W - 190 + i * 10, H - 18, "▮", 12, RED)}'
                 f'<animate attributeName="opacity" values=".2;1;.2" keyTimes="0;{(i + 1) / 17:.3f};1" calcMode="discrete" dur="{2 + k * .3:.1f}s" repeatCount="indefinite"/></g>')
    b.append(text(W - 34, 32, "↗", 14, GOLD))
    b.append(frame_overlay(W, H))
    return svg(W, H, "".join(b), f"Project {name}")


# ---------------------------------------------------------------- footer (side-view pass + chequered flag)

def footer(side):
    W, H = 1000, 200
    b = [f"<style>{BASE_CSS}.drive{{animation:drive 5s cubic-bezier(.6,0,.4,1) infinite}}"
         f"@keyframes drive{{0%{{transform:translateX(-420px)}}55%{{transform:translateX(1100px)}}100%{{transform:translateX(1100px)}}}}"
         f".wave text{{animation:wave 1.4s ease-in-out infinite alternate}}@keyframes wave{{from{{transform:translateY(-4px)}}to{{transform:translateY(4px)}}}}</style>",
         common_defs(), f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>']
    # road
    b.append(text(0, 168, "▔" * 140, 12, DIM, 'opacity=".5"', pitch=7.2))
    b.append(f'<g>{text(0, 186, "━━━━      " * 15, 12, GOLD, "opacity=\".35\"", pitch=7.2)}'
             f'<animateTransform attributeName="transform" type="translate" from="0 0" to="-72 0" dur=".25s" repeatCount="indefinite"/></g>')
    # side-view F40 passing by, with exhaust flames
    rows = [r for r in side if r.strip()]
    lo = min(len(r) - len(r.lstrip()) for r in rows)
    y0 = 166 - len(rows) * 5
    b.append(f'<g class="drive"><g fill="{RED}" filter="url(#glow)" font-size="5">')
    for i, r in enumerate(rows):
        t = r[lo:].rstrip()
        lead = len(t) - len(t.lstrip())
        b.append(f'<text x="{lead * 3:.0f}" y="{y0 + i * 5}" xml:space="preserve" textLength="{len(t.lstrip()) * 3:.1f}" lengthAdjust="spacingAndGlyphs">{esc(t.lstrip())}</text>')
    b.append("</g>")
    ey = y0 + (len(rows) - 6) * 5
    b.append(f'<g>{text(-14, ey, "≈≈~~", 11, GOLD, "filter=\"url(#glow2)\"")}<animate attributeName="opacity" values="1;.3;1;.6;1" dur=".2s" repeatCount="indefinite"/></g>')
    b.append(f'{text(-220, ey - 30, "─── ── ─  ", 12, DIM)}{text(-260, ey - 4, "──── ─ ── ", 12, DIM)}</g>')
    # chequered flag (columns wave with staggered delays)
    fx, fy = 860, 40
    b.append(text(fx - 8, fy - 8, "│", 14, DIM) + "".join(text(fx - 8, fy + 6 + j * 14, "│", 14, DIM) for j in range(8)))
    b.append('<g class="wave">')
    for c in range(8):
        col = "".join("█" if (c + r) % 2 == 0 else " " for r in range(5))
        for r, ch in enumerate(col):
            if ch != " ":
                b.append(text(fx + c * 13, fy + r * 14, "██", 13, INK, f'style="animation-delay:-{c * .17:.2f}s"', pitch=6.5))
    b.append("</g>")
    b.append(text(40, 44, "ARRIVEDERCI", 22, INK, 'font-weight="700" letter-spacing="8" filter="url(#glow)"'))
    b.append(text(42, 66, "thanks for the visit — drop a ★ if you liked the ride", 11, DIM))
    b.append(frame_overlay(W, H))
    return svg(W, H, "".join(b), "Footer — F40 driving past a chequered flag")


def main():
    os.makedirs(OUT, exist_ok=True)
    fr = frames(60)
    assert len(fr) == 60 and all(len(f) == ROWS for f in fr)
    files = {"hero.svg": hero(fr), "telemetry.svg": telemetry(), "gearbox.svg": gearbox(), "footer.svg": footer(fr[0])}
    for k, p in enumerate(PROJECTS):
        files[f"pit-{p[1]}.svg"] = card(*p, k)
    for name, data in files.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(data)
        print(f"{name:24s} {len(data) / 1024:7.1f} KB")


if __name__ == "__main__":
    main()
