"""Lighter paper shelf: no base shelf (the ream sits on the cubby floor), windowed side panels,
and slatted middle/top shelves with slots running front to back so sheets and plates slide without catching."""
from manifold3d import Manifold, CrossSection
import paper_shelf as ps
from paper_shelf import box, _ccw, IN_W, PT, D, ST, SPLIT_X, Z_MID, Z_TOP, GD, CL, T_TIP

WIN_R = 10.0
WIN_Y = (18.0, D - 18.0)
SLOT_W, SLAT, N_SLOTS = 18.0, 10.0, 4
SIDE_BAND, MID_BAND = 16.0, 22.0
SLOT_Y0, SLOT_BACK = 30.0, 16.0


def rrect(x0, x1, y0, y1, r):
    r = min(r, (x1 - x0) / 2 - 0.01, (y1 - y0) / 2 - 0.01)
    cs = CrossSection.square([x1 - x0 - 2 * r, y1 - y0]).translate([x0 + r, y0]) + \
        CrossSection.square([x1 - x0, y1 - y0 - 2 * r]).translate([x0, y0 + r])
    for cx in (x0 + r, x1 - r):
        for cy in (y0 + r, y1 - r):
            cs = cs + CrossSection.circle(r).translate([cx, cy])
    return cs


KEEP_BASE = True


def panel_windows():
    """Bays in the side panel (Y-Z), with ~10 mm of solid around every groove."""
    g = T_TIP / 2 + CL
    low = ps.Z_BASE + ST / 2 + g + 10.0 if KEEP_BASE else 12.0
    mid_lo = Z_MID + ST / 2 - g
    mid_hi = Z_MID + ST / 2 + g
    top_lo = Z_TOP + ST / 2 - g
    return [(low, mid_lo - 10.0), (mid_hi + 10.0, top_lo - 10.0)]


def panel_left():
    m = box(-PT, 0, 0, ps.D, 0, ps.H)
    for name, (z0, _) in ps.SHELVES.items():
        if name == "base" and not KEEP_BASE:
            continue
        m = m - ps.prism_xz(ps.tongue_profile(z0 + ST / 2, CL), -0.01, D - ps.STOP)
    m = m + box(-0.01, ps.PAD_W, 0, D, Z_TOP + ST, ps.H)
    m = m + box(-0.01, ps.PAD_W + ps.LEDGE_W, 0, D, ps.Z_LEDGE, ps.Z_LEDGE + ps.LEDGE_T)
    corner = box(-PT - 1, ps.PAD_W + ps.LEDGE_W + 1, -1, ps.TOP_R, ps.H - ps.TOP_R, ps.H + 1) - \
        Manifold.cylinder(PT + ps.PAD_W + ps.LEDGE_W + 4, ps.TOP_R, ps.TOP_R).rotate([0, 90, 0]).translate([-PT - 2, ps.TOP_R, ps.H - ps.TOP_R])
    m = m - corner
    for x0, sgn in ((-PT, 1), (ps.PAD_W, -1)):
        tri = CrossSection([_ccw([(x0 - sgn * 0.01, -0.01), (x0 + sgn * ps.EDGE_C, -0.01), (x0 - sgn * 0.01, ps.EDGE_C)])]).extrude(ps.H + 2).translate([0, 0, -1])
        m = m - tri
    # windows through the panel thickness (drawn in Y-Z, extruded along X)
    for z0, z1 in panel_windows():
        cs = rrect(WIN_Y[0], WIN_Y[1], z0, z1, WIN_R)
        m = m - Manifold.extrude(cs, PT + 2).rotate([90, 0, 90]).translate([-PT - 1, 0, 0])
    return m


def panel_right():
    return panel_left().mirror([1, 0, 0]).translate([IN_W, 0, 0])


def slot_xs():
    usable = SPLIT_X - MID_BAND - SIDE_BAND
    span = N_SLOTS * SLOT_W + (N_SLOTS - 1) * SLAT
    x = SIDE_BAND + (usable - span) / 2
    left = [x + i * (SLOT_W + SLAT) for i in range(N_SLOTS)]
    return left + [IN_W - xx - SLOT_W for xx in left]


_orig_whole = ps.shelf_whole


def shelf_whole(z0, ribs):
    m = _orig_whole(z0, ribs)
    d = D - ps.STOP - 0.3
    cs = None
    for x in slot_xs():
        s = rrect(x, x + SLOT_W, SLOT_Y0, d - SLOT_BACK, SLOT_W / 2)
        cs = s if cs is None else cs + s
    return m - cs.extrude(ST + 2).translate([0, 0, z0 - 1])


def shelf_halves(z0, ribs):
    orig = ps.shelf_whole
    ps.shelf_whole = shelf_whole
    try:
        return ps.shelf_halves(z0, ribs)
    finally:
        ps.shelf_whole = orig


def shelves():
    return {k: v for k, v in ps.SHELVES.items() if KEEP_BASE or k != "base"}


def panel_print(right=False):
    m = panel_left().rotate([0, -90, 0]) if not right else panel_right().rotate([0, 90, 0])
    return ps._drop(m)


def assembled(base_slatted=True):
    parts = [("panel_left", panel_left()), ("panel_right", panel_right())]
    for name, (z0, ribs) in shelves().items():
        l, r = shelf_halves(z0, ribs) if (name != "base" or base_slatted) else ps.shelf_halves(z0, ribs)
        parts += [(f"{name}_left", l), (f"{name}_right", r)]
    return parts
