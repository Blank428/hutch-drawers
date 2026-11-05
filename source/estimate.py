"""Rough slicer-style filament estimate: 2 perimeters (0.84 mm), ~4 solid top/bottom
layers, 15% infill, PLA 1.24 g/cm3. Bambu Studio will give the real number."""
import sys
sys.path.insert(0, '.')
from manifold3d import CrossSection, OpType
from drawer_module import *

PERIM = 1.26   # 3 wall loops
LAYER = 0.2
SOLID_LAYERS = 4
INFILL = 0.15
RHO = 1.24


def grams(m):
    b = m.bounding_box()
    z0, z1 = b[2], b[5]
    n = int((z1 - z0) / LAYER)
    zs = [z0 + LAYER * (i + 0.5) for i in range(n)]
    sl = [m.slice(z) for z in zs]
    empty = CrossSection()
    vol = 0.0
    for i, a in enumerate(sl):
        A = a.area()
        if A <= 0:
            continue
        core = a.offset(-PERIM)
        for k in range(1, SOLID_LAYERS + 1):
            for j in (i - k, i + k):
                other = sl[j] if 0 <= j < n else empty
                core = CrossSection.batch_boolean([core, other], OpType.Intersect)
        c = core.area()
        vol += ((A - c) + INFILL * c) * LAYER
    return vol / 1000 * RHO


if __name__ == "__main__":
    H = float(sys.argv[1]) if len(sys.argv) > 1 else 74.0
    D = float(sys.argv[2]) if len(sys.argv) > 2 else 232.0
    p = P(H=H, D=D)
    if D < 232:
        p.grid_y = 1
        p.windows = False
    tot = 0
    for n, fn in (("frame", frame_print), ("drawer", drawer_print), ("faceplate", faceplate_print)):
        g = grams(fn(p))
        tot += g
        print(f"{n:9s} {g:6.0f} g")
    print(f"module    {tot:6.0f} g")
