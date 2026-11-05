"""Printability check: list downward-facing areas steeper than 45 degrees that are not on the bed.
Small ones (holes, short bridges) are normal; anything large needs a design fix or supports."""
import sys
import numpy as np
sys.path.insert(0, '.')
from drawer_module import *


def overhangs(m, limit_deg=46.0):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    f = np.asarray(mesh.tri_verts)
    t = v[f]
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    a = np.linalg.norm(n, axis=1) / 2
    nz = n[:, 2] / np.maximum(np.linalg.norm(n, axis=1), 1e-12)
    zmin = t[:, :, 2].min(1)
    bad = (nz < -np.cos(np.radians(90 - limit_deg))) & (zmin > 0.3)
    # cluster bad triangles by rounded centroid region for reporting
    c = t[bad].mean(1)
    rep = {}
    for ci, ai, zi in zip(c, a[bad], zmin[bad]):
        k = (round(ci[0] / 20) * 20, round(ci[1] / 20) * 20, round(ci[2] / 10) * 10)
        rep.setdefault(k, [0, 1e9, 1e9, -1e9])
        rep[k][0] += ai
    # also report spans: width of each flat-down patch along x and y
    return a[bad].sum(), sorted(rep.items(), key=lambda kv: -kv[1][0])[:8], t[bad]


if __name__ == "__main__":
    p = P(H=float(sys.argv[1]) if len(sys.argv) > 1 else 74.0)
    for name, fn in (("frame", frame_print), ("drawer", drawer_print), ("faceplate", faceplate_print)):
        tot, top, tris = overhangs(fn(p))
        print(f"{name}: {tot:.0f} mm2 of >45deg downward faces")
        for k, v in top:
            print(f"   near (x,y,z)={k}: {v[0]:.0f} mm2")
        if len(tris):
            flat = tris[np.abs(np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])[:, 2]) > 0]
            xs = tris[:, :, 0]; ys = tris[:, :, 1]
