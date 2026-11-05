import sys; sys.path.insert(0, '.')
from drawer_module import *
from latch_v3 import latch3, latch3_print, nub_out_for, SETBACK
from overhangs import overhangs
iv = lambda a, b: (a ^ b).volume()
p = P(H=74)
F = frame(p); D = drawer(p)

def need(pre, pull, sgn=1, dx=0.0):
    """Inward flex the nub needs at this pull, drawer shifted sideways by dx (+ = toward +x)."""
    L = place(latch3(p, sgn, pre), p, pull).translate((dx, 0, 0))
    lo, hi = 0.0, 3.0
    if iv(F, L) < 0.01: return 0.0
    for _ in range(14):
        mid = (lo + hi) / 2
        if iv(F, L.translate((-sgn * mid, 0, 0))) < 0.01: hi = mid
        else: lo = mid
    return hi

for pre in (0.0, 0.2, 0.4):
    L = latch3(p, 1, pre)
    print(f"\npreload {pre}: nub_out {nub_out_for(p, pre):.2f}, solid parts {len(L.decompose())}, "
          f"fit in drawer overlap {iv(D, L):.2f} mm3 (crush rib only), lifted 0.5: {iv(D, L.translate((0,0,0.5))):.2f}")

    pulls = [0, 0.3, 0.6, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5, 20, 100, 160, 185, 186, 186.5, 187, 187.5]
    print("  flex needed (mm) at pull:", " ".join(f"{y}:{need(pre, y):.2f}" for y in pulls))
print("\ndrawer shifted 0.6 to the other side (worst case, standard preload):")
print("  ", " ".join(f"{y}:{need(0.2, y, 1, -0.6):.2f}" for y in [0, 2.5, 100, 186.5, 187.5]))
print("frame inner wall to groove floor = groove depth", p.groove_d)
for name, m in (("latch v3", latch3_print(p, 1, 0.2)),):
    tot, top, _ = overhangs(m); print(name, "overhang mm2", round(tot), [(k, round(float(v[0]), 1)) for k, v in top[:4]])
b = latch3_print(p, 1, 0.2).bounding_box(); print("print bbox", [round(v, 1) for v in b])
