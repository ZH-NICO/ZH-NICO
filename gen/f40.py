"""ASCII renderer for an F40-proportioned car.

Body = lofted cross-sections taken from the real car's dimensions
(4358 L x 1970 W x 1124 H mm, 2450 mm wheelbase). Points carry a material,
get z-buffered, shaded and outlined, and come out as (char, colour-class) grids.
"""
import numpy as np

COLS, ROWS = 160, 52
LEN = 4.36
FX, RX = 2.18 - 0.98, 2.18 - 3.43  # front / rear axle (x points forward)
WHEELS = [(FX, 0.314, 0.66, 0.905), (RX, 0.333, 0.60, 0.955)]  # x, radius, inner y, outer y

# station: d from nose, centre-top z, crown edge (y,z), shoulder (y,z), max width (y,z), rocker (y,z)
ST = np.array([
    # d     zc    yc    zce   ys    zs    yw     zw    yr    zr
    [0.00, 0.40, 0.40, 0.39, 0.66, 0.40, 0.80, 0.33, 0.78, 0.13],
    [0.12, 0.50, 0.40, 0.49, 0.70, 0.52, 0.90, 0.44, 0.88, 0.12],
    [0.50, 0.59, 0.36, 0.58, 0.72, 0.67, 0.95, 0.55, 0.93, 0.12],
    [0.98, 0.65, 0.34, 0.64, 0.73, 0.77, 0.965, 0.62, 0.95, 0.13],
    [1.40, 0.75, 0.40, 0.74, 0.76, 0.76, 0.965, 0.64, 0.95, 0.14],
    [1.47, 0.79, 0.64, 0.78, 0.79, 0.76, 0.965, 0.64, 0.95, 0.14],
    [1.82, 0.97, 0.58, 0.96, 0.82, 0.80, 0.97, 0.66, 0.95, 0.14],
    [2.16, 1.12, 0.53, 1.10, 0.84, 0.83, 0.975, 0.68, 0.955, 0.14],
    [2.65, 1.11, 0.51, 1.09, 0.86, 0.86, 0.98, 0.72, 0.96, 0.14],
    [2.85, 1.07, 0.42, 1.06, 0.80, 1.04, 0.985, 0.80, 0.965, 0.14],
    [3.43, 1.00, 0.42, 0.99, 0.81, 1.01, 0.985, 0.80, 0.965, 0.15],
    [3.95, 0.96, 0.44, 0.95, 0.83, 0.98, 0.98, 0.80, 0.96, 0.18],
    [4.30, 0.93, 0.45, 0.93, 0.84, 0.95, 0.97, 0.80, 0.95, 0.28],
    [4.36, 0.92, 0.45, 0.92, 0.84, 0.94, 0.96, 0.79, 0.94, 0.30],
])

BODY, GLASS, TIRE, RIM, TRIM, TAIL, LAMP, SHADOW, LOUVRE = range(9)


def station(d):
    """Profile keypoints as (y, z) for every d -> shape (len(d), 5, 2)."""
    c = [np.interp(d, ST[:, 0], ST[:, k]) for k in range(1, 10)]
    y = np.stack([0 * d, c[1], c[3], c[5], c[7]], 1)
    z = np.stack([c[0], c[2], c[4], c[6], c[8]], 1)
    return np.stack([y, z], 2)


def in_arch(x, z, pad=0.045):
    return np.any([(x - wx) ** 2 + (z - r) ** 2 < (r + pad) ** 2 for wx, r, _, _ in WHEELS], axis=0)


def build():
    P, N, M = [], [], []

    def add(p, n, m):
        p = np.stack([np.ravel(a) for a in p], 1).astype(float)
        n = np.stack([np.ravel(a) for a in n], 1).astype(float)
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        m = np.ravel(m) if np.ndim(m) else np.full(len(p), m)
        P.append(p); N.append(n); M.append(m.astype(int))

    # ---- lofted shell, one side, then mirrored
    d = np.arange(0, LEN + 1e-9, 0.009)
    kp = station(d)
    segs = [44, 30, 22, 52]
    pts, seg_id, seg_t = [], [], []
    for s, cnt in enumerate(segs):
        t = np.linspace(0, 1, cnt, endpoint=(s == 3))
        pts.append(kp[:, s, None, :] * (1 - t)[None, :, None] + kp[:, s + 1, None, :] * t[None, :, None])
        seg_id.append(np.full(cnt, s)); seg_t.append(t)
    prof = np.concatenate(pts, 1)
    sid, st = np.concatenate(seg_id), np.concatenate(seg_t)
    X = (2.18 - d)[:, None] * np.ones(prof.shape[1])
    Y, Z = prof[..., 0], prof[..., 1]
    G = np.stack([X, Y, Z], -1)
    nrm = np.cross(np.gradient(G, axis=1), np.gradient(G, axis=0))
    ref = np.stack([0 * X, Y, Z - 0.35], -1)
    nrm *= np.sign(np.sum(nrm * ref, -1, keepdims=True) + 1e-9)
    D = d[:, None] * np.ones_like(Y)
    S = sid[None, :] * np.ones_like(Y, int)
    T = st[None, :] * np.ones_like(Y)

    mat = np.full(Y.shape, BODY)
    mat[(S == 0) & (D > 1.47) & (D < 2.16)] = GLASS                                   # windscreen
    mat[(S == 1) & (D > 1.55) & (D < 2.62) & (T > 0.08) & (T < 0.92)] = GLASS          # side windows
    mat[(S == 0) & (D > 2.78) & (D < 3.95)] = LOUVRE                                    # slatted engine cover
    mat[(S <= 1) & (D > 2.66) & (D < 2.78)] = GLASS                                     # small rear window
    mat[(S == 0) & (D > 0.55) & (D < 0.9) & (np.abs(Y) > 0.16) & (np.abs(Y) < 0.30 - (D - 0.55) * 0.12)] = TRIM  # bonnet NACA ducts
    mat[(S == 0) & (D > 1.12) & (D < 1.38) & (np.abs(Y) < 0.30)] = TRIM                 # bonnet exit vent
    mat[(S <= 2) & (D > 0.04) & (D < 0.30) & (np.abs(Y) > 0.48) & (np.abs(Y) < 0.78)] = LAMP  # front lamps
    mat[(S == 2) & (D > 2.66) & (D < 3.02) & (T > 0.2)] = TRIM                          # rear-quarter intake
    mat[(S == 3) & (D > 2.0) & (D < 2.42) & (Z > 0.53) & (Z < 0.60) & (Z < 0.53 + (D - 2.0) * 0.25)] = TRIM  # door NACA
    mat[(S == 3) & (D > 2.82) & (D < 3.02) & (Z > 0.30) & (Z < 0.56)] = TRIM            # lower side intake
    keep = ~((S >= 2) & in_arch(X, Z))
    for side in (1, -1):
        add([X[keep], side * Y[keep], Z[keep]], [nrm[..., 0][keep], side * nrm[..., 1][keep], nrm[..., 2][keep]], mat[keep])

    # ---- nose and tail caps
    for dd, nx, tail in ((0.0, 1.0, False), (LEN, -1.0, True)):
        k5 = station(np.array([dd]))[0]
        yy, zz = np.meshgrid(np.linspace(-k5[3, 0], k5[3, 0], 170), np.arange(0.1, 1.0, 0.008))
        ztop = np.interp(np.abs(yy), k5[:4, 0], k5[:4, 1])
        zbot = np.interp(np.abs(yy), [0, k5[4, 0], k5[3, 0]], [k5[4, 1], k5[4, 1], k5[3, 1]])
        ok = (zz < ztop) & (zz > zbot)
        m = np.full(yy.shape, BODY)
        ay = np.abs(yy)
        if tail:
            m[(zz > 0.36) & (zz < ztop - 0.07)] = TRIM                               # black mesh panel
            for cy in (0.55, 0.76):
                m[(ay - cy) ** 2 + (zz - 0.66) ** 2 < 0.068 ** 2] = TAIL               # 4 round lamps
            for cy in (-0.12, 0.0, 0.12):
                m[(yy - cy) ** 2 + (zz - 0.44) ** 2 < 0.045 ** 2] = RIM                # triple exhaust
        else:
            m[(ay < 0.5) & (zz > 0.17) & (zz < 0.30)] = TRIM                         # front intake slot
            m[(ay > 0.58) & (ay < 0.74) & (zz > 0.17) & (zz < 0.27)] = TRIM          # brake ducts
        z0 = 0 * yy[ok]
        add([2.18 - dd + z0, yy[ok], zz[ok]], [nx + z0, z0, (0.6 if not tail else 0.05) + z0], m[ok])

    # ---- rear wing between fins, fins, mirrors
    xw, yw = np.meshgrid(2.18 - np.arange(4.02, 4.35, 0.008), np.linspace(-0.87, 0.87, 200))
    zw = 1.08 + (2.18 - 4.02 - xw) * 0.13
    add([xw, yw, zw], [-0.13 + 0 * xw, 0 * xw, 1 + 0 * xw], BODY)
    add([xw, yw, zw - 0.035], [0 * xw, 0 * xw, -1 + 0 * xw], TRIM)
    xf, zf = np.meshgrid(2.18 - np.arange(3.72, 4.36, 0.008), np.arange(0.85, 1.13, 0.008))
    ok = zf < np.interp(2.18 - xf, [3.72, 4.0, 4.36], [0.99, 1.10, 1.13])
    for side in (1, -1):
        for yv, sgn in ((0.93, 1), (0.87, -1)):
            z0 = 0 * xf[ok]
            add([xf[ok], side * yv + z0, zf[ok]], [z0, side * sgn + z0, z0], BODY)
        xm, zm = np.meshgrid(np.arange(0.40, 0.56, 0.008), np.arange(0.80, 0.90, 0.008))
        add([xm, side * 1.06 + 0 * xm, zm], [0.3 + 0 * xm, side + 0 * xm, 0.2 + 0 * xm], BODY)
        xm, ym = np.meshgrid(np.arange(0.40, 0.56, 0.008), np.arange(0.97, 1.06, 0.008))
        add([xm, side * ym, 0.90 + 0 * xm], [0 * xm, 0 * xm, 1 + 0 * xm], BODY)

    # ---- wheels: tread, sidewall, 5-spoke star rim, dark wheel wells
    for wx, r, yin, yout in WHEELS:
        rim_r = 0.216
        for side in (1, -1):
            a, yy = np.meshgrid(np.linspace(0, 2 * np.pi, 260), np.arange(yin, yout, 0.008))
            add([wx + r * np.cos(a), side * yy, r + r * np.sin(a)], [np.cos(a), 0 * a, np.sin(a)], TIRE)
            a, rr = np.meshgrid(np.linspace(0, 2 * np.pi, 320), np.arange(0, r, 0.006))
            ring = rr > rim_r
            ang = np.mod(a + np.pi / 2, 2 * np.pi / 5) - np.pi / 5
            spoke = np.abs(ang) < (0.13 + 0.10 * (1 - rr / rim_r))
            m = np.where(ring, TIRE, np.where(spoke | (rr < 0.055) | (rr > rim_r - 0.022), RIM, TRIM))
            yface = np.where(ring, yout, yout - 0.03)
            add([wx + rr * np.cos(a), side * yface, r + rr * np.sin(a)], [0 * a, side + 0 * a, 0 * a], m)
            xx, zz = np.meshgrid(np.arange(wx - r - 0.06, wx + r + 0.06, 0.008), np.arange(0.05, 2 * r + 0.06, 0.008))
            ok = in_arch(xx, zz, 0.05)
            z0 = 0 * xx[ok]
            add([xx[ok], side * (yin - 0.02) + z0, zz[ok]], [z0, side + z0, z0], TRIM)

    # ---- contact shadow on the ground
    xs, ys = np.meshgrid(np.arange(-2.45, 2.45, 0.012), np.arange(-1.15, 1.15, 0.012))
    ok = (xs / 2.45) ** 4 + (ys / 1.15) ** 4 < 1
    z0 = 0 * xs[ok]
    add([xs[ok], ys[ok], z0], [z0, z0, 1 + z0], SHADOW)
    return np.concatenate(P), np.concatenate(N), np.concatenate(M)


EDGE = {0: "-", 1: "\\", 2: "|", 3: "/"}
RAMP = "░░▒▒▓▓███"


def classify(mat, lum, spec, refl_up, x_world):
    cls = np.full(len(mat), "K", dtype=object)
    body = mat == BODY
    cls[body] = np.array(["B0", "B1", "B2", "B3"])[np.digitize(lum, [0.3, 0.55, 0.84])[body]]
    cls[body & (spec > 0.6)] = "B4"
    g = mat == GLASS
    cls[g] = np.where(refl_up[g] > 0.55, "G2", np.where(refl_up[g] > 0.15, "G1", "G0"))
    lv = mat == LOUVRE
    cls[lv] = np.where(np.sin(x_world[lv] * 52) > 0.35, "B1", "K")
    cls[mat == TIRE] = "T"
    cls[mat == RIM] = np.where(lum[mat == RIM] > 0.33, "R1", "R0")
    cls[mat == TAIL] = "L"
    cls[mat == LAMP] = "F"
    cls[mat == SHADOW] = "S"
    return cls


def render(thetas, cols=COLS, rows=ROWS, pitch=0.27, aspect=0.6, fit=0.94):
    P, N, M = build()
    light = np.array([-0.45, -0.55, 0.7]); light /= np.linalg.norm(light)
    cp, sp = np.cos(pitch), np.sin(pitch)
    Tm = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    view = np.array([0, -1.0, 0])  # towards the camera (camera on -y)
    up = Tm @ [0, 0, 1]
    proj = []
    for th in thetas:
        c, s = np.cos(th), np.sin(th)
        Mx = Tm @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        p = (P - [0, 0, 0.5]) @ Mx.T
        n = N @ Mx.T
        ndl = n @ light
        spec = np.clip((2 * ndl[:, None] * n - light) @ view, 0, 1) ** 24
        refl_up = (2 * (n @ view)[:, None] * n - view) @ up
        lum = np.clip(0.24 + 0.74 * np.clip(ndl, 0, 1) + 0.35 * spec, 0, 1)
        facing = (n[:, 1] < 0.05) | (M == SHADOW)
        f = 1 / (11.0 + p[:, 1])
        proj.append((p[:, 0] * f, -p[:, 2] * f * aspect, f, lum, spec, refl_up, facing, p[:, 1]))
    # one scale and centre for all frames so the car never jumps
    xs = np.concatenate([q[0][q[6]] for q in proj]); ys = np.concatenate([q[1][q[6]] for q in proj])
    k = fit * min((cols - 2) / (xs.max() - xs.min()), (rows - 1) / (ys.max() - ys.min()))
    ox, oy = cols / 2 - k * (xs.min() + xs.max()) / 2, rows / 2 - k * (ys.min() + ys.max()) / 2
    ramp = np.array(list(RAMP))
    out = []
    for qx, qy, f, lum, spec, refl_up, facing, depth in proj:
        sx, sy = (qx * k + ox).astype(int), (qy * k + oy).astype(int)
        ok = np.nonzero(facing & (sx >= 0) & (sx < cols) & (sy >= 0) & (sy < rows))[0]
        idx = ok[np.lexsort((f[ok], M[ok] != SHADOW))]  # shadow first, then far -> near
        yy, xx = sy[idx], sx[idx]
        gc = np.full((rows, cols), "", dtype=object)
        gch = np.full((rows, cols), " ", dtype=object)
        gd = np.full((rows, cols), 50.0)
        gm = np.full((rows, cols), -1)
        gc[yy, xx] = classify(M[idx], lum[idx], spec[idx], refl_up[idx], P[idx, 0])
        gch[yy, xx] = ramp[np.clip((lum[idx] * len(RAMP)).astype(int), 0, len(RAMP) - 1)]
        gd[yy, xx] = np.where(M[idx] == SHADOW, 50.0, depth[idx])
        gm[yy, xx] = M[idx]
        shadow = gm == SHADOW
        gch[shadow] = "░"
        car = (gm >= 0) & ~shadow
        # outlines: pixels whose neighbour is much farther (silhouette or depth step)
        pad = np.pad(gd, 1, mode="edge")
        nb = lambda dy, dx: pad[1 + dy:1 + dy + rows, 1 + dx:1 + dx + cols]
        edge = np.zeros_like(car)
        for (ay, ax), (by, bx) in (((0, 1), (0, -1)), ((1, 0), (-1, 0))):
            a, c2 = nb(ay, ax), nb(by, bx)
            # a real step, not just a sloped surface: one side jumps away much more than the other
            edge |= (np.maximum(a, c2) - gd > 0.22) & (a + c2 - 2 * gd > 0.2)
        edge &= car
        hy, hx = np.gradient(np.pad(gd, 1, mode="edge"))
        hy, hx = hy[1:-1, 1:-1] / aspect, hx[1:-1, 1:-1]
        ang = (np.degrees(np.arctan2(hy, hx)) + 90) % 180  # edge runs perpendicular to depth gradient
        bucket = ((ang + 22.5) // 45).astype(int) % 4
        for b, ch in EDGE.items():
            gch[edge & (bucket == b)] = ch
        gc[edge & np.isin(gc, ["B0", "B1", "B2"])] = "B3"
        out.append([list(zip(gch[r], gc[r])) for r in range(rows)])
    return out


def frames(n=48, **kw):
    return render([2 * np.pi * i / n + np.pi + 0.6 for i in range(n)], **kw)


if __name__ == "__main__":
    import sys
    for fr in render([0.6, 0.0, np.pi / 2, np.pi + 0.6]):
        sys.stdout.write("\n".join("|" + "".join(ch if c and c != "S" else " " for ch, c in row) + "|" for row in fr) + "\n" + "=" * 162 + "\n")
