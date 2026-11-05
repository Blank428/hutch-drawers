"""
Paper and build-plate shelf for the top-left hutch cubby (380 W x 240 D x ~149 H).

Freestanding, no screws. Two side panels with sliding-dovetail grooves; three shelves, each
printed as two halves that lock together with dovetail tabs, then slide in from the front.

  bottom   printer paper, a full ream (letter, laid sideways: 279 wide x 216 deep)
  middle   lined paper (loose-leaf)
  top      two build-plate slots: one plate on the top shelf, one on side ledges above it

Coordinates: X = width (0 = inner face of the left panel), Y = depth (0 = front),
Z = height (0 = cubby floor). Units: mm.
"""
from manifold3d import Manifold, CrossSection, set_circular_segments

set_circular_segments(48)

# ----------------------------------------------------------------------------- dimensions
IN_W = 285.0          # clear width between the panels (letter paper is 279)
PT = 7.0              # side panel thickness
D = 230.0             # depth (plates push back to the cubby wall and stick out ~17 mm)
H = 145.0             # unit height (cubby is ~149)
ST = 3.5              # shelf thickness
GD = 4.0              # groove depth into the panel
T_ROOT, T_TIP = 2.0, 3.5          # tongue thickness at the shelf edge and at its tip
CL = 0.2              # clearance, groove to tongue, per side
STOP = 4.0            # grooves stop this far from the back (shelves bottom out here)
RIB_H, RIB_T = 7.0, 4.0           # stiffening ribs under the middle and top shelves

BASE_Z = 1.0          # base shelf bottom (1 mm off the floor so the groove stays closed)
PAPER_ROOM = 63.0     # full ream (~50) + finger room, to the bottom of the front rib
LINED_ROOM = 38.0     # 200-sheet pack (~25) + finger room
SLOT1 = 9.0           # lower plate slot height, top shelf to ledge underside
LEDGE_T = 2.5
PAD_W = 13.0          # plate guides: 285 - 2*13 = 259 clear for the 257 mm plates
LEDGE_W = 8.0         # how far the ledge reaches past the guide (plate overlap)

# shelf heights (bottom face of each shelf plate)
Z_BASE = BASE_Z
Z_MID = Z_BASE + ST + PAPER_ROOM + RIB_H
Z_TOP = Z_MID + ST + LINED_ROOM + RIB_H
Z_LEDGE = Z_TOP + ST + SLOT1
SHELVES = {"base": (Z_BASE, False), "middle": (Z_MID, True), "top": (Z_TOP, True)}

SPLIT_X = IN_W / 2
TABS_Y = (32.0, 78.0, 113.0, 148.0, 194.0)   # dovetail tabs along the centre joint (clear of the ribs)
TAB_NECK, TAB_HEAD, TAB_LEN, TAB_CL = 10.0, 16.0, 10.0, 0.15


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def prism_xz(pts_xz, y0, y1):
    """Extrude a polygon drawn in X-Z along Y from y0 to y1."""
    cs = CrossSection([[(x, z) for x, z in pts_xz]])
    return cs.extrude(y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])


def _ccw(pts):
    a = sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))
    return pts if a > 0 else pts[::-1]


def tongue_profile(zc, grow=0.0):
    """Dovetail tongue/groove cross-section for the LEFT side, in X-Z (x<=0 is inside the panel)."""
    r, t = T_ROOT / 2 + grow, T_TIP / 2 + grow
    return _ccw([(0.6, zc - r), (0.0, zc - r), (-GD - grow, zc - t), (-GD - grow, zc + t), (0.0, zc + r), (0.6, zc + r)])


# ----------------------------------------------------------------------------- side panel
def panel_left():
    m = box(-PT, 0, 0, D, 0, H)
    for z0, _ in SHELVES.values():
        zc = z0 + ST / 2
        m = m - prism_xz(tongue_profile(zc, CL), -0.01, D - STOP)
    # plate guides above the top shelf, and the ledge for the upper plate
    m = m + box(-0.01, PAD_W, 0, D, Z_TOP + ST, H)
    m = m + box(-0.01, PAD_W + LEDGE_W, 0, D, Z_LEDGE, Z_LEDGE + LEDGE_T)
    # soften the front edges a touch
    return m


def panel_right():
    return panel_left().mirror([1, 0, 0]).translate([IN_W, 0, 0])


# ----------------------------------------------------------------------------- shelves
def shelf_whole(z0, ribs):
    zc = z0 + ST / 2
    d = D - STOP - 0.3
    m = box(0, IN_W, 0, d, z0, z0 + ST)
    left = prism_xz([(x, z) for x, z in tongue_profile(zc)], 0, d)
    m = m + left + left.mirror([1, 0, 0]).translate([IN_W, 0, 0])
    if ribs:
        for y0 in (0.0, d - RIB_T):
            m = m + box(1.0, IN_W - 1.0, y0, y0 + RIB_T, z0 - RIB_H, z0 + 0.01)
    return m


def _tabs(z0, grow=0.0):
    out = None
    for y in TABS_Y:
        pts = [(SPLIT_X - 0.5, y - TAB_NECK / 2 - grow), (SPLIT_X + TAB_LEN + grow, y - TAB_HEAD / 2 - grow),
               (SPLIT_X + TAB_LEN + grow, y + TAB_HEAD / 2 + grow), (SPLIT_X - 0.5, y + TAB_NECK / 2 + grow)]
        t = CrossSection([_ccw(pts)]).extrude(ST + 2 * grow).translate([0, 0, z0 - grow])
        out = t if out is None else out + t
    return out


def shelf_halves(z0, ribs):
    whole = shelf_whole(z0, ribs)
    big = 1000.0
    left = (whole ^ box(-big, SPLIT_X, -big, big, -big, big)) + (whole ^ _tabs(z0))
    right = (whole ^ box(SPLIT_X, big, -big, big, -big, big)) - _tabs(z0, TAB_CL)
    # a hairline gap between the ribs at the joint so the halves seat on the tabs, not the ribs
    if ribs:
        cut = box(SPLIT_X - 0.15, SPLIT_X + 0.15, -1, D, z0 - RIB_H - 1, z0)
        left, right = left - cut, right - cut
    return left, right


# ----------------------------------------------------------------------------- fit test
def fit_test():
    """Check the two joints before printing the real thing: a 30 mm slice of side panel with one
    groove, and a small shelf (tongue on its edge) printed as two halves joined by one dovetail tab."""
    zc, d = 12.0, 30 - STOP - 0.3
    pan = box(-PT, 0, 0, 30, 0, 24) - prism_xz(tongue_profile(zc, CL), -0.01, 30 - STOP)
    whole = box(0, 46, 0, d, zc - ST / 2, zc + ST / 2) + prism_xz(tongue_profile(zc), 0, d)
    sx, y = 18.0, d / 2
    pts = lambda g: _ccw([(sx - 0.5, y - TAB_NECK / 2 - g), (sx + TAB_LEN + g, y - TAB_HEAD / 2 - g),
                          (sx + TAB_LEN + g, y + TAB_HEAD / 2 + g), (sx - 0.5, y + TAB_NECK / 2 + g)])
    tab = lambda g: CrossSection([pts(g)]).extrude(ST + 2 * g).translate([0, 0, zc - ST / 2 - g])
    big = 1000.0
    a = (whole ^ box(-big, sx, -big, big, -big, big)) + (whole ^ tab(0))
    b = (whole ^ box(sx, big, -big, big, -big, big)) - tab(TAB_CL)
    return pan, a, b


# ----------------------------------------------------------------------------- print orientations
def _drop(m):
    b = m.bounding_box()
    return m.translate([-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]])


def panel_print(right=False):
    m = panel_left().rotate([0, -90, 0]) if not right else panel_right().rotate([0, 90, 0])
    return _drop(m)                    # outer face on the bed, grooves and ledge facing up


def shelf_print(m):
    return _drop(m.mirror([0, 0, 1]))   # top face on the bed, ribs up


def assembled():
    parts = [("panel_left", panel_left()), ("panel_right", panel_right())]
    for name, (z0, ribs) in SHELVES.items():
        l, r = shelf_halves(z0, ribs)
        parts += [(f"{name}_left", l), (f"{name}_right", r)]
    return parts


if __name__ == "__main__":
    print(f"shelf bottoms: base {Z_BASE:.1f}  middle {Z_MID:.1f}  top {Z_TOP:.1f}  ledge {Z_LEDGE:.1f}  unit H {H}")
    print(f"paper clear (to front rib): {Z_MID - RIB_H - (Z_BASE + ST):.1f}  lined clear: {Z_TOP - RIB_H - (Z_MID + ST):.1f}")
    print(f"lower plate slot {SLOT1}  upper slot to cubby ceiling 149: {149 - (Z_LEDGE + LEDGE_T):.1f}")
