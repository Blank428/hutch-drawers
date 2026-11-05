"""Tiny z-buffer renderer (orthographic) with flat shading and edge lines, for previews."""
import numpy as np
from PIL import Image


def _mesh(m):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].astype(np.float64)
    f = np.asarray(mesh.tri_verts).astype(np.int64)
    return v, f


def render(items, out, view=(1.0, -1.6, 1.0), up=(0, 0, 1), size=(1400, 1000), margin=0.06,
           bg=(250, 250, 248), light=(0.5, -0.9, 1.2), edges=True, fit=None):
    """items: list of (Manifold, rgb tuple 0-255)."""
    d = np.array(view, float); d /= np.linalg.norm(d)          # from target toward camera
    upv = np.array(up, float)
    right = np.cross(upv, d); right /= np.linalg.norm(right)
    camup = np.cross(d, right)
    L = np.array(light, float); L /= np.linalg.norm(L)

    tris, cols = [], []
    allv = []
    for m, c in items:
        v, f = _mesh(m)
        if len(f) == 0:
            continue
        allv.append(v)
        tris.append(v[f])
        cols.append(np.repeat(np.array(c, float)[None], len(f), 0))
    T = np.concatenate(tris)            # (n,3,3)
    C = np.concatenate(cols)
    V = np.concatenate(allv) if fit is None else fit

    def proj(P):
        return np.stack([P @ right, P @ camup, P @ d], -1)

    pv = proj(V)
    lo, hi = pv[:, :2].min(0), pv[:, :2].max(0)
    W, H = size
    span = hi - lo
    scale = min(W * (1 - 2 * margin) / span[0], H * (1 - 2 * margin) / span[1])
    off = np.array([W / 2, H / 2]) - (lo + hi) / 2 * scale

    PT = proj(T.reshape(-1, 3)).reshape(-1, 3, 3)
    sx = PT[..., 0] * scale + off[0]
    sy = H - (PT[..., 1] * scale + off[1])
    sz = PT[..., 2]

    n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    nn = np.linalg.norm(n, axis=1, keepdims=True); nn[nn == 0] = 1
    n = n / nn
    facing = n @ d
    diff = np.clip(n @ L, 0, 1)
    hv = (L + d); hv /= np.linalg.norm(hv)
    spec = np.clip(n @ hv, 0, 1) ** 40
    shade = (0.38 + 0.55 * diff)[:, None] * C + (spec * 40)[:, None]
    shade = np.clip(shade, 0, 255)

    zbuf = np.full((H, W), -np.inf)
    img = np.zeros((H, W, 3)); img[:] = bg
    nbuf = np.zeros((H, W, 3))
    idbuf = np.full((H, W), -1, np.int64)

    order = np.argsort(sz.mean(1))
    for i in order:
        if facing[i] <= 0:
            continue
        x, y, z = sx[i], sy[i], sz[i]
        x0, x1 = int(max(np.floor(x.min()), 0)), int(min(np.ceil(x.max()), W - 1))
        y0, y1 = int(max(np.floor(y.min()), 0)), int(min(np.ceil(y.max()), H - 1))
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(den) < 1e-12:
            continue
        a = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
        b = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
        c = 1 - a - b
        inside = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
        if not inside.any():
            continue
        zz = a * z[0] + b * z[1] + c * z[2]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (zz > sub)
        sub[upd] = zz[upd]
        img[y0:y1 + 1, x0:x1 + 1][upd] = shade[i]
        nbuf[y0:y1 + 1, x0:x1 + 1][upd] = n[i]
        idbuf[y0:y1 + 1, x0:x1 + 1][upd] = i

    if edges:
        # normal and depth discontinuities -> dark lines
        e = np.zeros((H, W), bool)
        dn = np.linalg.norm(np.diff(nbuf, axis=0), axis=-1) > 0.35
        e[1:] |= dn
        dn = np.linalg.norm(np.diff(nbuf, axis=1), axis=-1) > 0.35
        e[:, 1:] |= dn
        zf = np.where(np.isfinite(zbuf), zbuf, -1e6)
        thr = 2.0
        e[1:] |= np.abs(np.diff(zf, axis=0)) > thr
        e[:, 1:] |= np.abs(np.diff(zf, axis=1)) > thr
        img[e] = img[e] * 0.35 + np.array([25, 25, 25]) * 0.65
    im = Image.fromarray(img.astype(np.uint8))
    im.save(out)

    def to_px(P):
        P = np.atleast_2d(np.asarray(P, float))
        q = proj(P)
        return np.stack([q[:, 0] * scale + off[0], H - (q[:, 1] * scale + off[1])], -1)
    return to_px
