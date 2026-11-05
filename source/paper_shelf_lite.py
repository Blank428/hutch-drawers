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


# ----------------------------------------------------------------------------- stiff centre seam
# The plate-level dovetail tabs stop the halves pulling apart, but on their own the seam is a hinge.
# Two deep T-tabs (front, behind the finger notch, and back, into the back rib) run the full depth of
# shelf plate + a 7 mm keel. Pressing the halves together, the top of the seam is in compression and
# the T-head at the keel bottom takes the tension, so the seam carries bending like one solid shelf.
# The T-head's shoulder is tapered top to bottom: lowering the left half onto the right half, it has 0.5 mm
# of play at first and wedges down to 0.05 mm as the seam goes flush, so the joint seats tight with no slop.
DT_NECK_W, DT_HEAD_W = 8.0, 18.0     # in Y
DT_NECK_L, DT_HEAD_L = 6.0, 8.0      # in X, from the seam
DT_TAPER = 0.8                       # shoulder lead-in, over the full tab height
DT_CL_SHOULDER = 0.05                # seated play at the load-bearing shoulder (tune after the fit test)
DT_CL_SIDE, DT_CL_FRONT = 0.15, 0.3
KEEL_HALF = 20.0                     # keel runs SPLIT_X +/- 20
FRONT_KEEL = (20.0, 46.0)            # y range (behind the 20 mm notch)
DT_Y_FRONT = 33.0
DT_Y_BACK = 203.0
BACK_KEEL_Y0 = 188.0
PLATE_TABS_Y = (78.0, 113.0, 148.0)  # the remaining plate-level dovetails


def _keels(z0):
    d = D - ps.STOP - 0.3
    k = box(SPLIT_X - KEEL_HALF, SPLIT_X + KEEL_HALF, FRONT_KEEL[0], FRONT_KEEL[1], z0 - ps.RIB_H, z0 + 0.01)
    k = k + box(SPLIT_X - KEEL_HALF, SPLIT_X + KEEL_HALF, BACK_KEEL_Y0, d, z0 - ps.RIB_H, z0 + 0.01)
    return k


def _t_tab(yc, z0, socket=False):
    """Deep T-tab, owned by the left half; socket=True gives the cavity cut through the right half."""
    zb, zt = z0 - ps.RIB_H, z0 + ST
    cs, cf = (DT_CL_SIDE, DT_CL_FRONT) if socket else (0.0, 0.0)
    nw, hw = DT_NECK_W / 2 + cs, DT_HEAD_W / 2 + cs
    x0 = SPLIT_X - 0.5
    # neck + head in X-Y, extruded in slices so the shoulder (x = SPLIT_X + neck length) tapers with height:
    # neck length is DT_NECK_L at the top and DT_NECK_L + DT_TAPER at the bottom.
    out = None
    n = 6
    for i in range(n):
        za, zb_ = zb + (zt - zb) * i / n, zb + (zt - zb) * (i + 1) / n
        zm = (za + zb_) / 2
        nl = DT_NECK_L + DT_TAPER * (zt - zm) / (zt - zb) - (DT_CL_SHOULDER if socket else 0.0)
        xs = SPLIT_X + nl
        neck = CrossSection.square([xs - x0 + 0.01, 2 * nw]).translate([x0, yc - nw])
        # the socket's head cavity keeps a fixed front face, clear of the tab head at its longest
        hl = (SPLIT_X + DT_NECK_L + DT_TAPER + DT_HEAD_L + cf - xs) if socket else DT_HEAD_L
        head = CrossSection.square([hl, 2 * hw]).translate([xs, yc - hw])
        sl = (neck + head).extrude(zb_ - za + (0.02 if socket else 0.0)).translate([0, 0, za - (0.01 if socket else 0.0)])
        out = sl if out is None else out + sl
    if socket:  # open the socket fully through top and bottom
        out = out + _t_tab_ext(yc, z0)
    return out


def _t_tab_ext(yc, z0):
    """Extend the socket 1 mm past the top and bottom faces so it is a clean through-cut."""
    nw, hw = DT_NECK_W / 2 + DT_CL_SIDE, DT_HEAD_W / 2 + DT_CL_SIDE
    x0 = SPLIT_X - 0.5
    parts = []
    for z_a, z_b, nl in ((z0 - ps.RIB_H - 1, z0 - ps.RIB_H + 0.01, DT_NECK_L + DT_TAPER - DT_CL_SHOULDER), (z0 + ST - 0.01, z0 + ST + 1, DT_NECK_L - DT_CL_SHOULDER)):
        xs = SPLIT_X + nl
        cs = CrossSection.square([xs - x0, 2 * nw]).translate([x0, yc - nw]) + \
            CrossSection.square([SPLIT_X + DT_NECK_L + DT_TAPER + DT_HEAD_L + DT_CL_FRONT - xs, 2 * hw]).translate([xs, yc - hw])
        parts.append(cs.extrude(z_b - z_a).translate([0, 0, z_a]))
    return parts[0] + parts[1]


def _plate_tabs(z0, grow=0.0):
    out = None
    for y in PLATE_TABS_Y:
        pts = [(SPLIT_X - 0.5, y - ps.TAB_NECK / 2 - grow), (SPLIT_X + ps.TAB_LEN + grow, y - ps.TAB_HEAD / 2 - grow),
               (SPLIT_X + ps.TAB_LEN + grow, y + ps.TAB_HEAD / 2 + grow), (SPLIT_X - 0.5, y + ps.TAB_NECK / 2 + grow)]
        t = CrossSection([_ccw(pts)]).extrude(ST + 2 * grow).translate([0, 0, z0 - grow])
        out = t if out is None else out + t
    return out


def shelf_whole_stiff(z0, ribs):
    return shelf_whole(z0, ribs) + _keels(z0)


def shelf_halves(z0, ribs):
    """Ribbed (middle and top) shelves get the stiff seam; the base shelf rests on the floor and keeps the original joint."""
    if not ribs:
        orig = ps.shelf_whole
        ps.shelf_whole = shelf_whole
        try:
            return ps.shelf_halves(z0, ribs)
        finally:
            ps.shelf_whole = orig
    whole = shelf_whole_stiff(z0, ribs)
    big = 1000.0
    hair = box(SPLIT_X - 0.15, SPLIT_X + 0.15, -1, D, z0 - ps.RIB_H - 1, z0)
    tabs = _plate_tabs(z0) + _t_tab(DT_Y_FRONT, z0) + _t_tab(DT_Y_BACK, z0)
    left = (whole ^ box(-big, SPLIT_X, -big, big, -big, big)) - hair
    left = left + (whole ^ tabs)
    sock = _plate_tabs(z0, ps.TAB_CL) + _t_tab(DT_Y_FRONT, z0, True) + _t_tab(DT_Y_BACK, z0, True)
    right = (whole ^ box(SPLIT_X, big, -big, big, -big, big)) - hair - sock
    return left, right


def seam_test():
    """A 44 x 32 mm sample of the real middle shelf's seam (front deep T-tab and keel), for the fit test."""
    l, r = shelf_halves(ps.Z_MID, True)
    clip = box(SPLIT_X - 22, SPLIT_X + 22, 20.0, 52.0, -1000, 1000)
    return l ^ clip, r ^ clip
