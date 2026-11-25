"""Procedural low-poly F40-style wedge rendered to ASCII frames (donut.c style: point cloud + z-buffer + normal shading)."""
import numpy as np

RAMP = " .,-~:;=!*#$@"
COLS, ROWS = 110, 34


def smooth(a, b, t):
    t = np.clip((t - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def half_width(x):
    return 0.98 - 0.16 * smooth(1.4, 2.25, x) - 0.03 * smooth(-1.6, -2.25, x)


def deck(x, y):
    """Shoulder/deck height outside the cabin, with fender humps over the wheels."""
    z = np.interp(x, [-2.25, -1.9, -1.0, 0.3, 1.0, 1.8, 2.25], [0.98, 0.99, 0.95, 0.86, 0.8, 0.7, 0.58])
    hump = 0.07 * np.exp(-((x - 1.35) / 0.35) ** 2) + 0.06 * np.exp(-((x + 1.35) / 0.4) ** 2)
    return z + hump * smooth(0.35, 0.85, np.abs(y)) - 0.05 * (y / 0.98) ** 2


def roofline(x):
    return np.interp(x, [-1.95, -0.45, 0.25, 0.95, 1.1], [1.0, 1.13, 1.13, 0.82, 0.78])


def cabin_w(x):
    return np.interp(x, [-1.95, -0.5, 0.3, 1.0], [0.86, 0.55, 0.55, 0.62])


def top(x, y):
    m = 1 - smooth(cabin_w(x), cabin_w(x) + 0.2, np.abs(y))
    m = m * (x < 1.1) * (x > -1.95)
    return deck(x, y) + np.maximum(roofline(x) - deck(x, y), 0) * m, m


WHEELS = [(1.35, 0.33), (-1.35, 0.34)]


def in_arch(x, z):
    return np.any([(x - wx) ** 2 + (z - r) ** 2 < (r + 0.05) ** 2 for wx, r in WHEELS], axis=0)


def build():
    P, N, S = [], [], []  # points, normals, brightness scale

    def add(p, n, s=1.0):
        p, n = np.asarray(p, float).reshape(3, -1).T, np.asarray(n, float).reshape(3, -1).T
        n = n / np.linalg.norm(n, axis=1, keepdims=True)
        P.append(p); N.append(n); s = np.asarray(s, float).ravel()
        S.append(s if s.size == len(p) else np.full(len(p), s[0]))

    # top heightfield
    x, u = np.meshgrid(np.arange(-2.25, 2.25, 0.018), np.linspace(-1, 1, 110))
    y = u * half_width(x)
    z, m = top(x, y)
    e = 1e-3
    dzx = (top(x + e, y)[0] - top(x - e, y)[0]) / (2 * e)
    dzy = (top(x, y + e)[0] - top(x, y - e)[0]) / (2 * e)
    glass = (m > 0.6) & (((x > 0.25) & (x < 1.0)) | ((x < -0.45) & (x > -1.0)))
    louvre = (x < -1.0) & (x > -1.9) & (np.sin(x * 60) > 0.6) & (m > 0.3)
    s = np.where(glass, 0.45, 1.0) * np.where(louvre, 0.55, 1.0)
    add([x, y, z], [-dzx, -dzy, np.ones_like(x)], s)

    # side walls (cut out wheel arches, dark windows on cabin side, NACA intake)
    for side in (1, -1):
        x, t = np.meshgrid(np.arange(-2.25, 2.25, 0.018), np.linspace(0, 1, 70))
        w = half_width(x)
        zt = deck(x, w)
        z = 0.2 + t * (zt - 0.2)
        keep = ~in_arch(x, z)
        sc = np.where((x > -1.15) & (x < -0.45) & (z > 0.45) & (z < 0.68), 0.4, 1.0)
        sc = np.where(np.abs(z - 0.42) < 0.012, 0.5, sc)  # crease line
        add([x[keep], side * w[keep], z[keep]], [0 * x[keep], side + 0 * x[keep], -0.15 + 0.3 * t[keep]], sc[keep])
        # cabin side glass
        x, t = np.meshgrid(np.arange(-1.9, 1.05, 0.018), np.linspace(0, 1, 30))
        cw = cabin_w(x) + 0.1
        zb, zr = deck(x, cw), top(x, cw * 0 + 0)[0]
        keep = zr > zb + 0.02
        z = zb + t * (zr - zb)
        add([x[keep], side * cw[keep], z[keep]], [0 * x[keep], side + 0 * x[keep], 0.6 + 0 * x[keep]], 0.35)

    # nose and tail faces
    y, z = np.meshgrid(np.linspace(-1, 1, 90), np.linspace(0.2, 0.6, 26))
    yy = y * half_width(2.25)
    sc = np.where((z > 0.3) & (z < 0.4), 0.35, 1.0)  # intake slot
    add([2.25 + 0 * y, yy, z], [1 + 0 * y, 0 * y, 0.3 + 0 * y], sc)
    y, z = np.meshgrid(np.linspace(-1, 1, 90), np.linspace(0.25, 0.98, 40))
    yy = y * half_width(-2.25)
    lamps = np.zeros_like(y, bool)
    for cy in (-0.72, -0.48, 0.48, 0.72):
        lamps |= (yy - cy) ** 2 + (z - 0.75) ** 2 < 0.08 ** 2
    add([-2.25 + 0 * y, yy, z], [-1 + 0 * y, 0 * y, 0 * y], np.where(lamps, 1.6, 0.7))

    # rear wing: plate + end plates
    x, y = np.meshgrid(np.arange(-2.32, -1.98, 0.015), np.linspace(-0.97, 0.97, 110))
    add([x, y, 1.2 + 0 * x], [0.12 + 0 * x, 0 * x, 1 + 0 * x], 1.2)
    add([x, y, 1.18 + 0 * x], [0 * x, 0 * x, -1 + 0 * x], 0.5)
    for side in (1, -1):
        x, z = np.meshgrid(np.arange(-2.32, -1.95, 0.015), np.linspace(0.95, 1.22, 18))
        add([x, side * 0.97 + 0 * x, z], [0 * x, side + 0 * x, 0 * x], 0.9)

    # wheels: tread + 5-spoke face
    for wx, r in WHEELS:
        for side in (1, -1):
            a, yw = np.meshgrid(np.linspace(0, 2 * np.pi, 120), np.linspace(0.7, 0.95, 10))
            add([wx + r * np.cos(a), side * yw, r + r * np.sin(a)], [np.cos(a), 0 * a, np.sin(a)], 0.5)
            a, rr = np.meshgrid(np.linspace(0, 2 * np.pi, 160), np.linspace(0, r, 24))
            spoke = (np.cos(5 * a) > 0.55) | (rr < 0.07) | (rr > r * 0.72)
            add([wx + rr * np.cos(a), side * 0.95 + 0 * a, r + rr * np.sin(a)], [0 * a, side + 0 * a, 0 * a],
                np.where(rr > r * 0.86, 0.3, np.where(spoke, 1.1, 0.25)))
    return np.concatenate(P), np.concatenate(N), np.concatenate(S)


def frames(n=60, cols=COLS, rows=ROWS, aspect=0.6):
    P, N, S = build()
    light = np.array([-0.55, -0.6, 0.6]); light /= np.linalg.norm(light)
    pitch = 0.36
    cp, sp = np.cos(pitch), np.sin(pitch)
    T = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])  # camera pitch about screen-x
    proj = []
    for i in range(n):
        th = 2 * np.pi * i / n
        c, s = np.cos(th), np.sin(th)
        M = T @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        p = (P - [0, 0, 0.55]) @ M.T
        nn = N @ M.T
        diff = np.clip(nn @ light, 0, 1)
        refl = 2 * (nn @ light)[:, None] * nn - light
        spec = np.clip(-refl[:, 1], 0, 1) ** 18  # view dir is -y
        lum = np.clip((0.12 + 0.75 * diff) * S + 0.6 * spec * (S > 0.6), 0, 1)
        f = 1 / (9.0 + p[:, 1])  # camera on -y looking +y
        k = 9.0 * 16.5
        proj.append((p[:, 0] * f * k, -p[:, 2] * f * k * aspect, f, lum, nn[:, 1] < 0.1))
    xs = np.concatenate([q[0][q[4]] for q in proj]); ys = np.concatenate([q[1][q[4]] for q in proj])
    ox, oy = cols / 2 - (xs.min() + xs.max()) / 2, rows / 2 - (ys.min() + ys.max()) / 2
    out = []
    for qx, qy, f, lum, facing in proj:
        sx, sy = (qx + ox).astype(int), (qy + oy).astype(int)
        ok = facing & (sx >= 0) & (sx < cols) & (sy >= 0) & (sy < rows)
        grid = np.zeros((rows, cols), int)
        idx = np.argsort(f[ok])  # far to near so nearest wins
        grid[sy[ok][idx], sx[ok][idx]] = np.clip((lum[ok][idx] * (len(RAMP) - 1)).astype(int), 1, len(RAMP) - 1)
        out.append(["".join(RAMP[v] for v in row) for row in grid])
    return out


if __name__ == "__main__":
    fr = frames(12)
    for k in (0, 1, 2, 3):
        print("\n".join(fr[k]))
        print("-" * COLS)
