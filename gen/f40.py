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
    [0.00, 0.35, 0.40, 0.35, 0.66, 0.36, 0.80, 0.30, 0.78, 0.13],
    [0.12, 0.45, 0.40, 0.45, 0.70, 0.48, 0.90, 0.41, 0.88, 0.12],
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
DECAL = 9  # DECAL + badge colour index
DECAL_RGB = [(1.0, 0.80, 0.0), (0.03, 0.03, 0.03), (0.0, 0.50, 0.24), (0.93, 0.93, 0.9), (0.78, 0.09, 0.14)]
DECAL_HEX = ["#ffd200", "#111111", "#009246", "#f4f5f0", "#ce2b37"]

def shield_grid():
    """7x9 plain yellow shield with a tricolour top band, sized and placed like the real wing badges."""
    rows = ["GGWWWRR",
            "YYYYYYY",
            "YYYYYYY",
            "YYYYYYY",
            "YYYYYYY",
            "YYYYYYY",
            ".YYYYY.",
            "..YYY..",
            "...Y..."]
    code = {"Y": 0, "G": 2, "W": 3, "R": 4, ".": -1}
    return np.array([[code[c] for c in r] for r in rows])


def _smooth(a, k, axis):
    """Box filter with edge padding (rounds creases between loft stations / profile segments)."""
    pad = [(0, 0)] * a.ndim
    pad[axis] = (k // 2, k // 2)
    ap = np.pad(a, pad, mode="edge")
    c = np.cumsum(ap, axis=axis)
    c = np.concatenate([np.zeros_like(np.take(c, [0], axis=axis)), c], axis=axis)
    n = a.shape[axis]
    return (np.take(c, range(k, k + n), axis=axis) - np.take(c, range(0, n), axis=axis)) / k


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
    d = np.arange(0, LEN + 1e-9, 0.006)
    kp = station(d)
    segs = [64, 44, 32, 76]
    pts, seg_id, seg_t = [], [], []
    for s, cnt in enumerate(segs):
        t = np.linspace(0, 1, cnt, endpoint=(s == 3))
        pts.append(kp[:, s, None, :] * (1 - t)[None, :, None] + kp[:, s + 1, None, :] * t[None, :, None])
        seg_id.append(np.full(cnt, s)); seg_t.append(t)
    prof = np.concatenate(pts, 1)
    sid, st = np.concatenate(seg_id), np.concatenate(seg_t)
    X = (2.18 - d)[:, None] * np.ones(prof.shape[1])
    Y, Z = prof[..., 0], prof[..., 1]
    for _ in range(2):  # smooth surface: rounded shoulders, no faceting between stations
        Y, Z = _smooth(_smooth(Y, 15, 0), 7, 1), _smooth(_smooth(Z, 15, 0), 7, 1)
    Y[:, 0] = 0
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
    ay = np.abs(Y)
    naca = (S == 0) & (D > 0.80) & (D < 1.10) & (np.abs(ay - 0.2) < 0.015 + (D - 0.80) * 0.16)
    mat[naca] = TRIM                                                                    # two bonnet NACA ducts
    mat[(S <= 2) & (D > 0.06) & (D < 0.32) & (ay > 0.50) & (ay < 0.80)] = LAMP          # smoked headlamp glass
    lid_out = (D > 0.35) & (D < 0.67) & (ay > 0.46) & (ay < 0.81)
    lid_in = (D > 0.362) & (D < 0.658) & (ay > 0.472) & (ay < 0.798)
    mat[(S <= 2) & lid_out & ~lid_in] = TRIM                                            # pop-up lamp lid shut line
    mat[(S == 2) & (D > 2.66) & (D < 3.02) & (T > 0.2)] = TRIM                          # rear-quarter intake
    mat[(S == 3) & (D > 2.0) & (D < 2.42) & (Z > 0.53) & (Z < 0.60) & (Z < 0.53 + (D - 2.0) * 0.25)] = TRIM  # door NACA
    mat[(S == 3) & (D > 2.82) & (D < 3.02) & (Z > 0.30) & (Z < 0.56)] = TRIM            # lower side intake
    win = (S == 1) & (D > 1.55) & (D < 2.62) & (T > 0.06) & (T < 0.94)
    mat[win] = TRIM                                                                     # black window surround
    mat[(S == 1) & (D > 1.59) & (D < 2.58) & (T > 0.11) & (T < 0.9)] = GLASS            # side window
    shut = (S >= 2) & (mat == BODY) & (Z > 0.18) & ((np.abs(D - 1.66) < 0.006) | (np.abs(D - 2.59) < 0.006))
    mat[shut] = TRIM                                                                    # door shut lines
    mat[(S == 3) & (mat == BODY) & (np.abs(Z - 0.43) < 0.006) & (D > 1.36) & (D < 3.05)] = TRIM  # side crease
    mat[(S == 0) & (D > 0.025) & (D < 0.075) & (ay < 0.035)] = DECAL                    # small yellow nose badge
    keep = ~((S >= 2) & in_arch(X, Z))
    em = shield_grid()
    d0, d1, z0, z1 = 1.43, 1.52, 0.50, 0.625  # wing badge, just behind the front wheel arch
    on = (S == 3) & (D >= d0) & (D < d1) & (Z >= z0) & (Z < z1)
    v = np.clip(((z1 - Z) / (z1 - z0) * em.shape[0]).astype(int), 0, em.shape[0] - 1)
    for side in (1, -1):
        m = mat.copy()
        # read left-to-right from outside on both sides (front is on the left when looking at y>0)
        uu = (D - d0) if side == 1 else (d1 - D)
        u = np.clip((uu / (d1 - d0) * em.shape[1]).astype(int), 0, em.shape[1] - 1)
        e = em[v, u]
        m[on & (e >= 0)] = DECAL + e[on & (e >= 0)]
        add([X[keep], side * Y[keep], Z[keep]], [nrm[..., 0][keep], side * nrm[..., 1][keep], nrm[..., 2][keep]], m[keep])

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
            m[(ay < 0.62) & (zz > 0.155) & (zz < 0.27)] = TRIM                       # wide front intake
            m[(ay > 0.66) & (ay < 0.76) & (zz > 0.17) & (zz < 0.25)] = TRIM          # brake ducts
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
        xm, zm = np.meshgrid(np.arange(0.44, 0.54, 0.006), np.arange(0.84, 0.91, 0.006))
        add([xm, side * 1.04 + 0 * xm, zm], [0.3 + 0 * xm, side + 0 * xm, 0.2 + 0 * xm], BODY)
        xm, ym = np.meshgrid(np.arange(0.44, 0.54, 0.006), np.arange(0.97, 1.04, 0.006))
        add([xm, side * ym, 0.91 + 0 * xm], [0 * xm, 0 * xm, 1 + 0 * xm], BODY)

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


def _env(r_up):
    """Studio environment seen in reflections: bright softbox above, dark horizon, warm floor."""
    sky = np.array([0.95, 0.96, 1.0]); hor = np.array([0.10, 0.10, 0.13]); floor = np.array([0.10, 0.02, 0.01])
    t = np.clip(r_up, -1, 1)[:, None]
    up = hor + (sky - hor) * np.clip(t * 1.6, 0, 1) ** 1.5
    return np.where(t > 0, up, hor + (floor - hor) * np.clip(-t * 3, 0, 1))


def render_px(thetas, W, H, pitch=0.2, dist=9.0, fit=0.96, ss=2, bg=(0.03, 0.03, 0.04)):
    """Shaded RGB images (H, W, 3) in 0..1 for each yaw angle; one shared scale so frames never jump."""
    P, N, M = build()
    keep = M != SHADOW
    P, N, M = P[keep], N[keep], M[keep]
    key = np.array([-0.5, -0.6, 0.62]); key /= np.linalg.norm(key)
    fill = np.array([0.7, -0.4, 0.2]); fill /= np.linalg.norm(fill)
    cp, sp = np.cos(pitch), np.sin(pitch)
    Tm = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    up = Tm @ [0, 0, 1]
    v = np.array([0, -1.0, 0])
    views = []
    for th in thetas:
        c, s = np.cos(th), np.sin(th)
        Mx = Tm @ np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        p = (P - [0, 0, 0.5]) @ Mx.T
        n = N @ Mx.T
        f = 1 / (dist + p[:, 1])
        views.append((p, n, f))
    xs = np.concatenate([p[:, 0] * f for p, n, f in views]); ys = np.concatenate([-p[:, 2] * f for p, n, f in views])
    Ws, Hs = W * ss, H * ss
    k = fit * min((Ws - 2) / (xs.max() - xs.min()), (Hs - 2) / (ys.max() - ys.min()))
    ox, oy = Ws / 2 - k * (xs.max() + xs.min()) / 2, Hs / 2 - k * (ys.max() + ys.min()) / 2
    out = []
    for p, n, f in views:
        ndv = np.clip(-(n[:, 1]), 0, 1)
        diff = np.clip(n @ key, 0, 1)
        dfill = np.clip(n @ fill, 0, 1)
        r = 2 * (n @ v)[:, None] * n - v
        r_up = r @ up
        env = _env(r_up)
        spec = np.clip((2 * (n @ key)[:, None] * n - key) @ v, 0, 1)
        fres = 0.06 + 0.94 * (1 - ndv) ** 5
        col = np.zeros((len(P), 3))
        paint = np.array([0.86, 0.07, 0.025])
        body = (M == BODY) | ((M == LOUVRE) & (np.sin(P[:, 0] * 52) > 0.2))
        col[body] = (paint * (0.16 + 0.95 * diff[body, None] + 0.25 * dfill[body, None])
                     + env[body] * (0.10 + 0.6 * fres[body, None]) + 1.2 * spec[body, None] ** 40)
        g = M == GLASS
        seat = np.clip((1.06 - P[g, 2]) / 0.2, 0, 1)[:, None]  # red interior showing through the lower glass
        col[g] = (np.array([0.05, 0.06, 0.07]) + seat * (1 - fres[g, None]) * np.array([0.55, 0.05, 0.03])
                  + env[g] * (0.22 + 0.6 * fres[g, None]) + 1.5 * spec[g, None] ** 60)
        t = M == TIRE
        col[t] = 0.05 + 0.07 * diff[t, None] + 0.04 * env[t]
        rm = M == RIM
        col[rm] = np.array([0.93, 0.93, 0.95]) * (0.62 + 0.35 * env[rm] + 0.35 * diff[rm, None]) + spec[rm, None] ** 20
        tr = (M == TRIM) | ((M == LOUVRE) & ~body)
        col[tr] = 0.025 + 0.05 * diff[tr, None] + 0.05 * env[tr]
        col[M == TAIL] = [1.0, 0.1, 0.06]
        lp = M == LAMP
        dl, yl = 2.18 - P[lp, 0], np.abs(P[lp, 1])
        reflector = ((dl > 0.11) & (dl < 0.27) & (yl > 0.55) & (yl < 0.75)).astype(float)[:, None]
        col[lp] = (np.array([0.08, 0.10, 0.12]) + env[lp] * (0.35 + 0.5 * fres[lp, None]) + 1.5 * spec[lp, None] ** 50
                   + reflector * np.array([0.45, 0.48, 0.5]))
        for i, rgb in enumerate(DECAL_RGB):
            dm = M == DECAL + i
            col[dm] = np.array(rgb) * (0.8 + 0.25 * diff[dm, None])
        lit = (M != TAIL) & (M != LAMP) & (M != RIM) & (M < DECAL)
        col[lit] *= (0.55 + 0.45 * np.clip((P[lit, 2] - 0.06) / 0.4, 0, 1))[:, None]  # ground occlusion
        col = np.clip(col, 0, 1)
        facing = n[:, 1] < 0.05
        sx = (p[:, 0] * f * k + ox).astype(int); sy = (-p[:, 2] * f * k + oy).astype(int)
        ok = np.nonzero(facing & (sx >= 0) & (sx < Ws - 1) & (sy >= 0) & (sy < Hs - 1))[0]
        ok = ok[np.argsort(f[ok])]  # far -> near, nearest written last wins
        img = np.zeros((Hs, Ws, 3)); dep = np.full((Hs, Ws), 99.0)
        for dy in (0, 1):  # 2x2 splat closes sampling holes
            for dx in (0, 1):
                yy, xx = sy[ok] + dy, sx[ok] + dx
                zz = p[ok, 1]
                # nearer splat may not be overwritten by a farther neighbour: write per pass, keep min depth
                closer = zz < dep[yy, xx] + 0.02
                img[yy[closer], xx[closer]] = col[ok][closer]
                dep[yy[closer], xx[closer]] = np.minimum(dep[yy[closer], xx[closer]], zz[closer])
        cover = dep < 50
        # crisp contour: darken real depth steps (second difference), not sloped surfaces
        pad = np.pad(np.where(cover, dep, 60.0), 1, mode="edge")
        nb = lambda a, b: pad[1 + a:1 + a + Hs, 1 + b:1 + b + Ws]
        edge = np.zeros_like(cover)
        for (a1, b1), (a2, b2) in (((0, 1), (0, -1)), ((1, 0), (-1, 0))):
            A, B = nb(a1, b1), nb(a2, b2)
            edge |= (np.maximum(A, B) - dep > 0.12) & (A + B - 2 * dep > 0.1)
        img[edge & cover] *= 0.35
        # downsample ss x ss with coverage -> anti-aliased edges against the background
        img = img.reshape(H, ss, W, ss, 3).mean((1, 3))
        a = cover.reshape(H, ss, W, ss).mean((1, 3))
        rgb = np.where(a[..., None] > 0, img / np.maximum(a[..., None], 1e-6), 0)
        rgb = rgb * a[..., None] + np.array(bg) * (1 - a[..., None])
        out.append((np.clip(rgb, 0, 1), a))
    return out


def quantize(images, colors=28, fixed=DECAL_RGB, tol=0.2):
    """Shared palette across frames -> index grids (-1 = background) and hex palette.

    Pixels close to one of the `fixed` colours (the emblem) keep that exact colour so
    the median cut cannot wash it out.
    """
    from PIL import Image
    fx = np.array([[min(1, c * 0.95) for c in rgb] for rgb in fixed])
    vis = np.concatenate([rgb[a > 0.25] for rgb, a in images])
    near = np.min(np.linalg.norm(vis[:, None, :] - fx[None], axis=2), 1) < tol
    sample = Image.fromarray((vis[~near][None] * 255).astype(np.uint8))
    pal_img = sample.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    pal = np.array(pal_img.getpalette()[:colors * 3]).reshape(-1, 3)
    grids = []
    for rgb, a in images:
        g = np.array(Image.fromarray((rgb * 255).astype(np.uint8)).quantize(palette=pal_img, dither=Image.Dither.NONE)).astype(int)
        dist = np.linalg.norm(rgb[..., None, :] - fx, axis=-1)
        k = dist.argmin(-1)
        hit = dist.min(-1) < tol
        g[hit] = colors + k[hit]
        g[a <= 0.25] = -1
        grids.append(g)
    hexes = ["#%02x%02x%02x" % tuple(c) for c in pal] + ["#%02x%02x%02x" % tuple(int(v * 255) for v in c) for c in fx]
    return grids, hexes


if __name__ == "__main__":
    from PIL import Image
    imgs = render_px([np.pi + 0.65, 0.0, np.pi / 2, 0.65], 260, 110)
    Image.fromarray((np.vstack([i for i, _ in imgs]) * 255).astype(np.uint8)).resize((780, 1320), Image.NEAREST).save(
        r"C:/Users/nicos/AppData/Local/Temp/claude/1344df2ecd16dca1/ca94d143-088c-4fca-b8c5-ae0c813ef31b/scratchpad/px.png")
