"""
Stop latch v3: a drop-in replacement for the v2 latch. It fits the drawers and frames
that are already printed (same root, same pocket, same window, same groove, same hump).

Why v2 felt weak
  The v2 nub stuck out 1.4 mm past the drawer wall. The drawer has 0.6 mm of side play
  and the frame's groove starts 0.6 mm out from the drawer wall, so the nub only reached
  0.8 mm into the groove with the drawer centred, and as little as 0.2 mm when the drawer
  sat to one side. The detent hump and the stop wall both rely on that engagement, so
  the click was faint and the stop sometimes slipped.

What v3 changes
  - The nub reaches all the way to the groove floor plus a small preload, so it rides
    lightly on the floor the whole way. That keeps full 1.2 mm engagement with the stop
    wall and the hump no matter which way the drawer shifts, and both nubs centre the drawer.
  - Thinner arm (1.6 mm) so the extra flex stays at low stress. Best in PETG.
  - Nub set back 0.6 mm so it sits just behind the hump when shut (about 0.3 mm of play).
  - Flat-topped nub (its top is an upward face, so it prints fine) to stay inside the
    groove's height.
  - Release hook pulled in to leave more room for Gridfinity bins.
  - Three preloads: soft 0.0, standard 0.2, firm 0.4 mm.
"""
import sys
sys.path.insert(0, '.')
from drawer_module import P, box, hull, poly_extrude_z, _latch_root_profile, _drop, Manifold

ARM_T = 1.6
SETBACK = 0.6
TAB_IN = 2.5


def nub_out_for(p: P, preload: float) -> float:
    # tip at the groove floor (frame inner wall + groove depth) plus the preload
    return (p.Wi / 2 + p.groove_d + preload) - p.Wd / 2


def latch3(p: P, sgn=1, preload=0.2):
    yt, r0, r1 = p.latch_y
    z0, z1 = p.latch_z
    xo = sgn * p.Wd / 2
    xi = sgn * (p.Wd / 2 - p.dw_side)
    xa = sgn * (p.Wd / 2 - ARM_T)
    arm = box(min(xo, xa), max(xo, xa), yt, r0 + 0.01, z0, z1)
    root = poly_extrude_z(_latch_root_profile(p, sgn), z0, z1)
    m = arm + root

    # nub: square front face (hard stop), 45 deg back face, flat top, 45 deg underside
    n = nub_out_for(p, preload)
    za, zb = p.nub_z
    y0 = yt + 0.3 + SETBACK
    y1 = y0 + p.nub_len
    xb = xo - sgn * 0.3                       # buried 0.3 into the arm for a clean union
    zbot = za - (n + 0.3)                     # 45 degree underside, tip bottom at za
    m = m + hull([(xb, y0, zbot), (xb, y1 + n, zbot), (xb, y0, zb), (xb, y1 + n, zb),
                  (xo + sgn * n, y0, za), (xo + sgn * n, y1, za),
                  (xo + sgn * n, y0, zb), (xo + sgn * n, y1, zb)])

    # release hook on the inside of the tip (fin + forward lip; 45 deg undersides)
    tt, th = p.tab_t, p.tab_h
    ti = TAB_IN
    xin = xa
    ya, yb = yt, yt + tt
    m = m + hull([(xin + sgn * 0.3, ya, z1 - th - ti), (xin + sgn * 0.3, yb, z1 - th - ti),
                  (xin + sgn * 0.3, ya, z1), (xin + sgn * 0.3, yb, z1),
                  (xin - sgn * ti, ya, z1 - th), (xin - sgn * ti, yb, z1 - th),
                  (xin - sgn * ti, ya, z1), (xin - sgn * ti, yb, z1)])
    lx0, lx1 = xin - sgn * ti, xin - sgn * (ti - 1.2)
    ll = p.hook_len
    m = m + hull([(lx0, ya + 0.5, z1 - th), (lx1, ya + 0.5, z1 - th), (lx0, ya + 0.5, z1), (lx1, ya + 0.5, z1),
                  (lx0, ya - ll, z1 - th + ll), (lx1, ya - ll, z1 - th + ll), (lx0, ya - ll, z1), (lx1, ya - ll, z1)])

    # same crush rib as v2: light press fit in the pocket
    xm = (xo + xi) / 2
    m = m + box(xm - 0.3, xm + 0.3, r1 - 0.01, r1 + p.latch_clear + 0.1, z0 + 1.0, z1 - 0.5)
    return m


def latch3_print(p: P, sgn=1, preload=0.2):
    return _drop(latch3(p, sgn, preload))


# ----------------------------------------------------------------------------- ganged print plate
# Latches standing on edge alone tip over or let go of the bed. A gang prints them side by
# side joined by small snap-off tie bars, so the whole row braces itself like one wide part.
PITCH = 7.6        # latch spacing across the row
TIE = 1.0          # tie bar section
NECK = 0.5         # thinner neck where each tie meets a latch, so it snaps off clean


def _tie(x0, x1, y, z):
    """Tie bar along x from x0 to x1 (x0 < x1) at (y, z), necked at both ends."""
    h, n = TIE / 2, NECK / 2
    body = box(x0 + 0.6, x1 - 0.6, y - h, y + h, z - h, z + h)
    ends = []
    for xa, xb in ((x0 - 0.05, x0 + 0.6), (x1 - 0.6, x1 + 0.05)):
        ends.append(box(xa, xb, y - n, y + n, z - h, z + h))   # full height so the bar is anchored from its first layer
    return body + ends[0] + ends[1]


def latch3_gang(p: P, count: int, sgn=1, preload=0.2):
    """`count` latches of one hand in a row, in print orientation, tied together."""
    one = latch3(p, 1, preload)
    yt, r0, r1 = p.latch_y
    z0, z1 = p.latch_z
    xo = p.Wd / 2
    xa = p.Wd / 2 - ARM_T
    m = None
    for k in range(count):
        c = one.translate((k * PITCH, 0, 0))
        m = c if m is None else m + c
        if k < count - 1:
            # from this latch's arm outer face to the next latch's arm inner face
            x0, x1 = k * PITCH + xo, (k + 1) * PITCH + xa
            for y in (yt + 11.0, yt + 19.0):
                for z in (z0 + 3.0, z1 - 3.5):
                    m = m + _tie(x0, x1, y, z)
    if sgn < 0:
        m = m.mirror((1, 0, 0))
    return _drop(m)
