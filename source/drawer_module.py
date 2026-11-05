"""
Hutch drawer module v2: parametric frame + drawer + slide-on faceplate + label tag
+ TPU foot pads + TPU top caps.

Assembly coordinates: X = width (centred on 0), Y = depth (0 = frame front face,
+Y toward the back of the hutch), Z = height (0 = bottom of the module). Units: mm.

To make another tier, change H (module height). Everything else follows.

v2 changes from v1
  - drawer rides on two low rails in the frame floor instead of dragging its whole floor
  - drawer bottom edge chamfered so first-layer squish (elephant's foot) can't rub
  - closed-position detent: a small hump in the stop groove clicks the drawer shut
  - drawer back wall dropped 3 mm so only the side walls ever touch the ceiling
    (no snagging on the ceiling windows when the drawer tips at full extension)
  - lead-in chamfer on the ceiling front edge
  - faceplate extends over the stacking gap: every reveal between fronts is 1 mm
  - recessed label slot on every faceplate + separate label tag
  - TPU top spacers on the top bumps leave ~0.3 mm to the cubby ceiling. A top module on its
    own tips forward with only ~10 g in a fully opened drawer; the spacers stop it after
    0.3 mm, long before the 1.2 mm bumps can unseat. Each column is stacked outside the
    cubby and slid in as one unit (sliding a module in over the bumps inside the cubby would
    need 1.2 mm of lift that isn't there).

Print orientations (all without supports):
  frame      standing on its back (open front facing up)
  drawer     upright
  faceplate  face down
  label tag  flat
  pads, caps TPU, flat
"""
import math
from dataclasses import dataclass
from manifold3d import Manifold, CrossSection, JoinType, OpType, set_circular_segments

set_circular_segments(48)


# ----------------------------------------------------------------------------- params
@dataclass
class P:
    # module envelope (cubbies are 380 W x 240 D; two modules side by side,
    # faceplates end up about 3.5 mm back from the cubby's front edge)
    W: float = 188.0          # frame outer width
    D: float = 232.0          # frame outer depth
    H: float = 74.0           # frame outer height (not counting the 1.2 mm top bumps)

    # frame walls
    ts: float = 2.4           # side walls
    tb: float = 2.4           # top and bottom walls
    tback: float = 2.4        # back wall

    # rails in the frame floor (the drawer rides on these)
    rail_h: float = 1.0
    rail_w: float = 6.0       # at the base
    rail_top: float = 4.0     # flat top width
    rail_inset: float = 12.0  # rail centre, measured in from the inner side wall

    # drawer
    side_clear: float = 0.6   # per side, drawer to frame
    rear_clear: float = 1.0   # drawer back to frame back when closed
    ceil_clear: float = 0.6   # drawer wall top to frame ceiling
    standoff: float = 13.0    # faceplate back to drawer front: the finger pocket
    dw_side: float = 1.8
    dw_front: float = 2.2
    dw_back: float = 1.8
    base: float = 1.0         # solid floor under the Gridfinity sockets
    bottom_chamfer: float = 0.6
    back_drop: float = 3.0    # back wall top sits this far below the side walls
    grid_x: int = 4
    grid_y: int = 5

    # stop: a nub on each drawer side rides in a groove in the frame side wall; the groove
    # ends in a square wall near the front = a hard stop.
    # To take a drawer out: pull to the stop, pinch both release fins inward, pull.
    # Stop latch: a separate small part (2 per drawer) that slides down into a dovetail pocket
    # at the back of each drawer side wall. It prints standing on its bottom edge, so its
    # bending and the stop load both run along the print layers, and it has no overhangs.
    # Rooted at the back, free end pointing forward with the nub on it: the stop load is
    # compression along the arm, offset outward, which presses the nub deeper into the groove.
    # Reprint just the latches to tune the click or the stop; the drawers stay as they are.
    latch_arm: float = 24.0          # free arm length (y): ~16 MPa in-layer at 1 mm release flex
    latch_root: float = 7.0          # root length held in the pocket (y)
    latch_h: float = 16.0            # latch height (z); its top sits flush with the drawer wall top
    latch_dt: float = 3.0            # dovetail block depth (inward, x)
    latch_clear: float = 0.15        # pocket clearance per side
    nub_len: float = 2.0             # flat top length of the nub (y)
    nub_out: float = 1.4             # nub protrusion past the drawer side wall
    groove_d: float = 1.2            # groove depth into the frame side wall
    stop_wall_y: float = 8.0         # frame-y of the groove's square front end (the hard stop)
    tab_t: float = 4.0               # release fin on the inside of each latch's free end
    tab_in: float = 3.5              # stays clear of Gridfinity bins in the back corners
    tab_h: float = 10.0
    hook_len: float = 4.0            # lip running forward from the fin (fingernail slot)

    # closed detent: hump in the groove just in front of the nub's closed position
    hump_h: float = 1.0              # 0.6 mm of interference with the nub
    hump_half: float = 2.0           # half length of the hump base
    hump_gap: float = -0.75          # hump position tweak; tuned for ~0.45 mm play when shut

    # faceplate
    fp_t: float = 4.5
    fp_gap: float = 0.5          # per side, so every gap between fronts is 1 mm
    post_x: float = 48.0         # dovetail posts at +-post_x
    post_relief: float = 0.4     # bottom 0.5 mm of each post inset (elephant's foot relief)
    dt_clear: float = 0.25       # dovetail clearance per side
    notch_w: float = 70.0
    notch_h: float = 24.0

    # label slot (recess in the faceplate front) and tag
    label_w: float = 50.0
    label_h: float = 14.0
    label_d: float = 1.0
    label_below_notch: float = 6.0
    tag_clear: float = 0.2       # per side
    tag_t: float = 1.0
    label_v3: bool = False       # v3 slot: chamfered mouth + fingernail notch for lifting tags out
    label_mouth: float = 0.4     # mouth chamfer (also cancels first-layer squish at the slot edge)
    notch_r: float = 2.5
    notch_d: float = 1.8

    # stacking interlock / pads / caps
    bump_r: float = 3.0
    bump_h: float = 1.2
    rec_r: float = 3.3
    rec_d: float = 1.5
    bump_inset_x: float = 15.0
    bump_inset_y: float = 20.0
    pad_out: float = 0.6         # how far a foot pad stands proud of the module bottom
    cap_r: float = 5.5

    # filament saving windows (hidden surfaces)
    windows: bool = True

    # ---- derived
    @property
    def Hi(self):
        return self.H - 2 * self.tb

    @property
    def Wi(self):
        return self.W - 2 * self.ts

    @property
    def Di(self):
        return self.D - self.tback

    @property
    def Wd(self):
        return self.Wi - 2 * self.side_clear

    @property
    def Dd(self):
        return self.Di - self.standoff - self.rear_clear

    @property
    def Hd(self):
        return self.Hi - self.rail_h - self.ceil_clear

    @property
    def zd(self):
        """Module z of the drawer's bottom face."""
        return self.tb + self.rail_h

    @property
    def slab(self):
        return self.base + 4.65

    @property
    def usable(self):
        """Clear height inside the drawer above the Gridfinity socket tops (to the frame ceiling)."""
        return self.Hi - self.rail_h - self.slab

    @property
    def rail_x(self):
        return self.Wi / 2 - self.rail_inset

    # latch geometry (drawer coords)
    @property
    def latch_y(self):  # (tip, root start, root end)
        r1 = self.Dd - self.dw_back - 0.3
        r0 = r1 - self.latch_root
        return (r0 - self.latch_arm, r0, r1)

    @property
    def latch_z(self):
        return (self.Hd - self.latch_h, self.Hd)

    @property
    def nub_z(self):
        a, b = self.latch_z
        return (a + 3.5, b - 4.0)

    @property
    def nub_front(self):  # drawer-y of the nub's square front face
        return self.latch_y[0] + 0.3

    @property
    def groove_z(self):
        a, b = self.nub_z
        return (self.zd + a - self.nub_out - 1.0, self.zd + b + 1.0)

    @property
    def nub_front_closed(self):  # frame-y of the nub front face with the drawer shut
        return self.standoff + self.nub_front

    @property
    def groove_front(self):
        return self.stop_wall_y

    @property
    def inside_at_stop(self):
        """Drawer length still inside the frame when it hits the stop."""
        return self.stop_wall_y + (self.Dd - self.nub_front)

    # faceplate vertical extent in module coords (modules stack flush: bumps 1.2 sit fully in
    # 1.5 deep recesses, so there is no gap between stacked frames)
    @property
    def fp_z(self):
        return (self.fp_gap, self.H - self.fp_gap)


# ----------------------------------------------------------------------------- helpers
def _area(pts):
    a = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return a / 2


def _ccw(pts):
    return pts if _area(pts) > 0 else pts[::-1]


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube((x1 - x0, y1 - y0, z1 - z0)).translate((x0, y0, z0))


def rrect(w, d, r):
    r = max(min(r, w / 2 - 0.01, d / 2 - 0.01), 0.01)
    return CrossSection.square((w - 2 * r, d - 2 * r), center=True).offset(r, JoinType.Round)


def rbox(cx, cy, w, d, z0, z1, r):
    return Manifold.extrude(rrect(w, d, r), z1 - z0).translate((cx, cy, z0))


def poly_extrude_z(pts, z0, z1):
    return Manifold.extrude(CrossSection([_ccw(pts)]), z1 - z0).translate((0, 0, z0))


def prism_yz(pts_yz, x0, x1):
    """Polygon in the (y, z) plane, extruded along X from x0 to x1."""
    m = Manifold.extrude(CrossSection([_ccw(list(pts_yz))]), x1 - x0)
    return m.transform([[0, 0, 1, x0], [1, 0, 0, 0], [0, 1, 0, 0]])


def hull(pts):
    return Manifold.hull_points(pts)


# ----------------------------------------------------------------------------- gridfinity
def gf_pocket():
    """One Gridfinity baseplate socket, bottom at z=0, top at z=4.65 (profile 0.7/1.8/2.15)."""
    e = 0.01
    upper = Manifold.batch_hull([rbox(0, 0, 42.0, 42.0, 4.65, 4.65 + e, 4.0),
                                 rbox(0, 0, 37.7, 37.7, 2.5, 2.5 + e, 1.85)])
    vertical = rbox(0, 0, 37.7, 37.7, 0.7, 2.5 + e, 1.85)
    lower = Manifold.batch_hull([rbox(0, 0, 37.7, 37.7, 0.7, 0.7 + e, 1.85),
                                 rbox(0, 0, 36.3, 36.3, 0.0, e, 1.15)])
    above = rbox(0, 0, 42.0, 42.0, 4.65, 6.5, 4.0)
    return upper + vertical + lower + above


# ----------------------------------------------------------------------------- frame
def frame(p: P):
    W, D, H = p.W, p.D, p.H
    f = box(-W / 2, W / 2, 0, D, 0, H) - box(-W / 2 + p.ts, W / 2 - p.ts, -1, p.Di, p.tb, H - p.tb)

    gz0, gz1 = p.groove_z

    if p.windows and D > 100:
        # Frame prints standing on its back, so "up" while printing is toward the front (-Y).
        # Every window gets a 45 degree point at its front end so nothing has to bridge.
        # Windows are split by 8 mm cross-ribs so no part of the frame stands more than
        # ~60 mm tall on its own while printing (long free strips whip on a bed-slinger).
        RIB = 8.0
        NWIN = 4

        def spans(y0, y1, min_len=0.0):
            n = NWIN
            while n > 1 and (y1 - y0 - (n - 1) * RIB) / n < min_len:
                n -= 1
            L = (y1 - y0 - (n - 1) * RIB) / n
            return [(y0 + i * (L + RIB), y0 + i * (L + RIB) + L) for i in range(n)]

        zl, zh = 12.0, gz0 - 4.0
        rows = [(zl, zh)]
        if zh - zl > 50:  # tall side walls: two rows of windows with a rib between
            zm = (zl + zh) / 2
            rows = [(zl, zm - RIB / 2), (zm + RIB / 2, zh)]
        for (za_, zb_) in rows:
            if zb_ - za_ <= 12:
                continue
            hh = (zb_ - za_) / 2
            for (yf, yb) in spans(24.0, D - 18.0, hh + 8):
                win = [(yb, za_), (yb, zb_), (yf + hh, zb_), (yf, za_ + hh), (yf + hh, za_)]
                f = f - prism_yz(win, -W / 2 - 1, -W / 2 + p.ts + 1)
                f = f - prism_yz(win, W / 2 - p.ts - 1, W / 2 + 1)
        # floor and ceiling slots (kept clear of the rails and of the drawer side walls)
        xo = min(70.0, p.rail_x - p.rail_w / 2 - 5.0)
        for (xa, xb) in ((-xo, -14.0), (14.0, xo)):
            hw = (xb - xa) / 2
            for (yf, yb) in spans(30.0, D - 26.0):
                pts = [(xa, yb), (xb, yb), (xb, yf + hw), ((xa + xb) / 2, yf), (xa, yf + hw)]
                for (z0, z1) in ((-1, p.tb + 1), (H - p.tb - 1, H + 1)):
                    f = f - poly_extrude_z(pts, z0, z1)
        bw = Manifold.extrude(rrect(W - 36, H - 30, 6), p.tback + 2)
        f = f - bw.transform([[1, 0, 0, 0], [0, 0, 1, p.Di - 1], [0, 1, 0, H / 2]])

    # rails: trapezoid section, ramped up at the front so the drawer climbs on smoothly
    rh, rw, rt = p.rail_h, p.rail_w, p.rail_top
    for sgn in (-1, 1):
        xc = sgn * p.rail_x
        z0 = p.tb - 0.01
        pts = []
        for (y, h) in ((1.2, 0.0), (5.0, rh), (p.Di + 0.01, rh)):
            hw_top = rt / 2 if h > 0 else rw / 2
            pts += [(xc - rw / 2, y, z0), (xc + rw / 2, y, z0),
                    (xc - hw_top, y, p.tb + h), (xc + hw_top, y, p.tb + h)]
        f = f + hull(pts[:8]) + hull(pts[4:])

    # stop grooves in both side walls, from the back up to the stop ramp
    g = p.groove_d
    yg = p.groove_front
    for sgn in (-1, 1):
        xin = sgn * p.Wi / 2
        xg = sgn * (p.Wi / 2 + g)
        xa, xb = min(xin - sgn * 0.2, xg), max(xin - sgn * 0.2, xg)
        f = f - box(xa, xb, yg, p.Di + 0.5, gz0, gz1)
        # square front end of the groove = hard stop (in print orientation, a 1.2 mm ledge)
        # closed detent hump, sitting on the groove floor just in front of the closed nub
        ye = p.nub_front_closed - p.hump_gap
        yp = ye - p.hump_half
        ys = ye - 2 * p.hump_half
        xw = sgn * (p.Wi / 2 + g + 0.3)            # buried in the wall for a clean union
        xpk = sgn * (p.Wi / 2 + g - p.hump_h)      # hump peak
        hump = hull([(xw, ys, gz0), (xw, ys, gz1), (xw, ye, gz0), (xw, ye, gz1),
                     (xpk, yp, gz0 + 0.5), (xpk, yp, gz1 - 0.5)])
        f = f + hump
        # lead-in chamfer at the front opening (side walls)
        lead = hull([(xin - sgn * 0.01, 2.0, p.tb - 0.5), (xin - sgn * 0.01, 2.0, H - p.tb + 0.5),
                     (sgn * (p.Wi / 2 + 1.4), -0.1, p.tb - 0.5), (sgn * (p.Wi / 2 + 1.4), -0.1, H - p.tb + 0.5),
                     (xin - sgn * 0.01, -0.1, p.tb - 0.5), (xin - sgn * 0.01, -0.1, H - p.tb + 0.5)])
        f = f - lead
    # lead-ins on the floor and ceiling front edges
    f = f - hull([(-p.Wi / 2, -0.1, p.tb + 0.01), (p.Wi / 2, -0.1, p.tb + 0.01),
                  (-p.Wi / 2, -0.1, p.tb - 0.8), (p.Wi / 2, -0.1, p.tb - 0.8),
                  (-p.Wi / 2, 0.8, p.tb + 0.01), (p.Wi / 2, 0.8, p.tb + 0.01)])
    f = f - hull([(-p.Wi / 2, -0.1, H - p.tb - 0.01), (p.Wi / 2, -0.1, H - p.tb - 0.01),
                  (-p.Wi / 2, -0.1, H - p.tb + 0.8), (p.Wi / 2, -0.1, H - p.tb + 0.8),
                  (-p.Wi / 2, 0.8, H - p.tb - 0.01), (p.Wi / 2, 0.8, H - p.tb - 0.01)])

    # stacking interlock: bumps on top, matching recesses underneath (recesses take TPU pads)
    for sx in (-1, 1):
        for y in (p.bump_inset_y, D - p.bump_inset_y):
            x = sx * (W / 2 - p.bump_inset_x)
            f = f + Manifold.cylinder(p.bump_h, p.bump_r, p.bump_r - 0.4).translate((x, y, H))
            f = f - Manifold.cylinder(p.rec_d + 1, p.rec_r).translate((x, y, -1))
    return f


# ----------------------------------------------------------------------------- drawer
def drawer(p: P):
    """Drawer in its own coords: front face of the front wall at y=0, bottom at z=0."""
    Wd, Dd, Hd = p.Wd, p.Dd, p.Hd
    s = p.standoff
    c = p.bottom_chamfer
    yc_, dl = (Dd - s) / 2, Dd + s
    # body runs forward to the faceplate; bottom edge chamfered (elephant's foot relief)
    d = Manifold.batch_hull([rbox(0, yc_, Wd - 2 * c, dl - 2 * c, 0, 0.01, 2.0 - c * 0.6),
                             rbox(0, yc_, Wd, dl, c, Hd, 2.0)])
    d = d - box(-Wd / 2 + p.dw_side, Wd / 2 - p.dw_side, p.dw_front, Dd - p.dw_back, p.slab, Hd + 1)
    # finger pocket in front of the front wall (floor 1.6 mm thick)
    d = d - box(-Wd / 2 + p.dw_side, Wd / 2 - p.dw_side, -s - 1, 0, 1.6, Hd + 1)
    # back wall dropped below the side walls so it never rides the frame ceiling
    d = d - box(-Wd / 2 + p.dw_side, Wd / 2 - p.dw_side, Dd - p.dw_back - 0.5, Dd + 1,
                Hd - p.back_drop, Hd + 1)

    # Gridfinity sockets, grid pushed to the front wall with 0.6 mm slack
    x0 = -p.grid_x * 42 / 2 + 21
    y0 = p.dw_front + 0.6 + 21
    pk = gf_pocket()
    pockets = [pk.translate((x0 + i * 42, y0 + j * 42, p.base))
               for i in range(p.grid_x) for j in range(p.grid_y)]
    d = d - Manifold.batch_boolean(pockets, OpType.Add)

    # latch pockets: open the side wall where the latch arm sits, and cut a dovetail pocket
    # (inside a boss on the inner face) that holds the latch root
    for sgn in (-1, 1):
        d = d + latch_boss(p, sgn)
        d = d - latch_window(p, sgn)
        d = d - latch_pocket(p, sgn)

    # dovetail posts that carry the faceplate
    for xc in (-p.post_x, p.post_x):
        pts = [(xc - 5, 0.5), (xc + 5, 0.5), (xc + 5, -(s - 3)), (xc + 3.5, -s),
               (xc + 4.5, -(s + 2.4)), (xc - 4.5, -(s + 2.4)), (xc - 3.5, -s), (xc - 5, -(s - 3))]
        post = poly_extrude_z(pts, 0.5, Hd)
        inset = CrossSection([_ccw(pts)]).offset(-p.post_relief, JoinType.Miter)
        post = post + Manifold.extrude(inset, 0.51)
        d = d + post
    return d


# ----------------------------------------------------------------------------- stop latch
def _latch_root_profile(p: P, sgn, grow=0.0):
    """Root cross-section in the (x, y) plane, drawer coords. Plate band through the wall plus
    a dovetail block on the inside that widens inward, so the root can't pull out sideways."""
    _, r0, r1 = p.latch_y
    xo = sgn * p.Wd / 2
    xi = sgn * (p.Wd / 2 - p.dw_side)
    xd = sgn * (p.Wd / 2 - p.dw_side - p.latch_dt)
    g = grow
    xs = xi - sgn * g  # shoulder faces get clearance too
    pts = [(xo + sgn * g, r0 - g), (xo + sgn * g, r1 + g),
           (xs, r1 + g), (xs, r1 - 1.5 + g),
           (xd - sgn * g, r1 + g), (xd - sgn * g, r0 - g),
           (xs, r0 + 1.5 - g), (xs, r0 - g)]
    return pts


def latch(p: P, sgn=1):
    """One stop latch in drawer coords (installed position) for side sgn."""
    yt, r0, r1 = p.latch_y
    z0, z1 = p.latch_z
    xo = sgn * p.Wd / 2
    xi = sgn * (p.Wd / 2 - p.dw_side)
    arm = box(min(xo, xi), max(xo, xi), yt, r0 + 0.01, z0, z1)
    root = poly_extrude_z(_latch_root_profile(p, sgn), z0, z1)
    m = arm + root
    # nub on the outside of the tip: square front face, 45 deg back face, chamfered top/bottom
    n = p.nub_out
    za, zb = p.nub_z
    y0n = p.nub_front
    y1n = y0n + p.nub_len
    zc0 = za - (n + 0.3) * 1.15
    m = m + hull([(xo - sgn * 0.3, y0n, zc0), (xo - sgn * 0.3, y1n + n, zc0),
                  (xo - sgn * 0.3, y0n, zb + n * 0.5), (xo - sgn * 0.3, y1n + n, zb + n * 0.5),
                  (xo + sgn * n, y0n, za), (xo + sgn * n, y1n, za),
                  (xo + sgn * n, y0n, zb), (xo + sgn * n, y1n, zb)])
    # release hook on the inside of the tip: a fin plus a lip running forward, leaving a
    # 2.3 mm slot against the wall. Hook a fingernail into the slot and pull toward the
    # middle. All undersides at 45 degrees so it prints without support.
    tt, ti, th = p.tab_t, p.tab_in, p.tab_h
    ya, yb = yt, yt + tt
    m = m + hull([(xi + sgn * 0.3, ya, z1 - th - ti), (xi + sgn * 0.3, yb, z1 - th - ti),
                  (xi + sgn * 0.3, ya, z1), (xi + sgn * 0.3, yb, z1),
                  (xi - sgn * ti, ya, z1 - th), (xi - sgn * ti, yb, z1 - th),
                  (xi - sgn * ti, ya, z1), (xi - sgn * ti, yb, z1)])
    lx0, lx1 = xi - sgn * ti, xi - sgn * (ti - 1.2)
    ll = p.hook_len
    m = m + hull([(lx0, ya + 0.5, z1 - th), (lx1, ya + 0.5, z1 - th), (lx0, ya + 0.5, z1), (lx1, ya + 0.5, z1),
                  (lx0, ya - ll, z1 - th + ll), (lx1, ya - ll, z1 - th + ll), (lx0, ya - ll, z1), (lx1, ya - ll, z1)])
    # crush rib on the root's back face: 0.1 mm press fit that wedges the root against the
    # pocket, so the latch stays put when the drawer is out of its frame
    xm = (xo + xi) / 2
    m = m + box(xm - 0.3, xm + 0.3, r1 - 0.01, r1 + p.latch_clear + 0.1, z0 + 1.0, z1 - 0.5)
    return m


def latch_window(p: P, sgn):
    yt, r0, r1 = p.latch_y
    z0, z1 = p.latch_z
    xo = sgn * (p.Wd / 2 + 1)
    xi = sgn * (p.Wd / 2 - p.dw_side - 0.01)
    # the arm's slot through the wall, open at the top, 0.4 mm around the arm
    return box(min(xo, xi), max(xo, xi), yt - 0.6, r0 + 0.01, z0 - 0.4, p.Hd + 1)


def latch_boss(p: P, sgn):
    _, r0, r1 = p.latch_y
    z0, z1 = p.latch_z
    xi = sgn * (p.Wd / 2 - p.dw_side + 0.2)
    xb = sgn * (p.Wd / 2 - p.dw_side - p.latch_dt - 1.6)
    ya, yb = r0 - 1.6, p.Dd - 0.5
    zb = z0 - 0.15 - 1.6
    depth = abs(xb - xi)
    # 45 degree underside so it prints without support
    return hull([(xi, ya, zb - depth), (xi, yb, zb - depth),
                 (xb, ya, zb), (xb, yb, zb),
                 (xi, ya, p.Hd), (xi, yb, p.Hd), (xb, ya, p.Hd), (xb, yb, p.Hd)])


def latch_pocket(p: P, sgn):
    z0, _ = p.latch_z
    c = p.latch_clear
    pk = poly_extrude_z(_latch_root_profile(p, sgn, c), z0 - c, p.Hd + 1)
    # extra relief at the pocket floor for the latch's first-layer flare
    pk = pk + poly_extrude_z(_latch_root_profile(p, sgn, c + 0.3), z0 - c, z0 + 0.5)
    return pk


def latch_print(p: P):
    """Right-hand latch standing on its bottom edge. The left one is its mirror image
    (print the mirrored file, or mirror it in the slicer)."""
    return _drop(latch(p, 1))


def drawer_assembled(p: P):
    return drawer(p) + latch(p, 1) + latch(p, -1)


# ----------------------------------------------------------------------------- faceplate
def faceplate(p: P):
    """Faceplate in drawer coords (so it can be checked against the drawer)."""
    s = p.standoff
    Wf = p.W - 2 * p.fp_gap
    m0, m1 = p.fp_z
    z0, z1 = m0 - p.zd, m1 - p.zd
    Hf = z1 - z0
    yb = -s
    yf = -(s + p.fp_t)
    ch = 0.8
    back_part = Manifold.extrude(rrect(Wf, Hf, 3.0), p.fp_t - ch)
    front_part = Manifold.extrude(rrect(Wf - 2 * ch, Hf - 2 * ch, 2.5), 0.01).translate((0, 0, p.fp_t - 0.01))
    plate = Manifold.batch_hull([back_part, front_part])
    plate = plate.transform([[1, 0, 0, 0], [0, 0, -1, yb], [0, 1, 0, (z0 + z1) / 2]])

    # dovetail channels: open at the bottom, closed at the top. The faceplate slides down
    # from above and hangs on the post tops (channel ceiling = post top = Hd).
    c = p.dt_clear
    for xc in (-p.post_x, p.post_x):
        pts = [(xc - 3.5 - c, -(s - 1.0)), (xc + 3.5 + c, -(s - 1.0)), (xc + 3.5 + c, -s),
               (xc + 4.5 + c, -(s + 2.4 + c)), (xc - 4.5 - c, -(s + 2.4 + c)), (xc - 3.5 - c, -s)]
        plate = plate - poly_extrude_z(pts, z0 - 1, p.Hd)

    notch = Manifold.extrude(rrect(p.notch_w, p.notch_h * 2, 8.0), 20).transform(
        [[1, 0, 0, 0], [0, 0, -1, yb + 5], [0, 1, 0, z1]])
    plate = plate - notch

    # label slot: fixed distance below the notch, so labels line up along a row
    lz = z1 - p.notch_h - p.label_below_notch - p.label_h / 2
    rec = Manifold.extrude(rrect(p.label_w, p.label_h, 1.5), p.label_d + 1).transform(
        [[1, 0, 0, 0], [0, 0, 1, yf - 1], [0, 1, 0, lz]])
    if p.label_v3:
        mc = p.label_mouth
        mouth = Manifold.batch_hull([
            Manifold.extrude(rrect(p.label_w + 2 * mc, p.label_h + 2 * mc, 1.5 + mc), 0.01),
            Manifold.extrude(rrect(p.label_w, p.label_h, 1.5), 0.01).translate((0, 0, mc))])
        rec = rec + mouth.translate((0, 0, -0.005)).transform([[1, 0, 0, 0], [0, 0, 1, yf], [0, 1, 0, lz]])
        notch = Manifold.cylinder(p.notch_d + 1, p.notch_r).transform(
            [[1, 0, 0, p.label_w / 2 - 0.6], [0, 0, 1, yf - 1], [0, 1, 0, lz]])
        rec = rec + notch
    return plate - rec


def label_tag(p: P):
    w, h = p.label_w - 2 * p.tag_clear, p.label_h - 2 * p.tag_clear
    e = 0.3
    return Manifold.batch_hull([rbox(0, 0, w, h, 0, p.tag_t - e, 1.3),
                                rbox(0, 0, w - 2 * e, h - 2 * e, p.tag_t - 0.01, p.tag_t, 1.0)])


def tpu_pad(p: P):
    return Manifold.cylinder(p.rec_d + p.pad_out, p.rec_r + 0.05)


def tpu_cap(p: P, h: float):
    """Cap that presses over a top bump; h = its height above the module's top surface.
    Modelled in print orientation: the face that touches the cubby ceiling is on the bed
    (chamfered edge), the tapered pocket for the bump opens upward, so no bridging."""
    r = p.cap_r
    ch = 0.6
    body = Manifold.batch_hull([Manifold.cylinder(0.01, r - ch), Manifold.cylinder(h - ch, r).translate((0, 0, ch))])
    depth = p.bump_h + 0.2
    pocket = Manifold.cylinder(depth + 0.01, p.bump_r - 0.4 + 0.12, p.bump_r + 0.12).translate((0, 0, h - depth))
    return body - pocket


# ----------------------------------------------------------------------------- placement
def place(m, p: P, pull=0.0, z=0.0):
    return m.translate((0, p.standoff - pull, p.zd + z))


def frame_print(p: P):
    m = frame(p).transform([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, p.D]])  # back on the bed
    return _drop(m)


def drawer_print(p: P):
    return _drop(drawer(p))


def faceplate_print(p: P):
    m = faceplate(p).transform([[-1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0]])  # face down
    return _drop(m)


def _drop(m):
    b = m.bounding_box()
    return m.translate((-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]))


# ----------------------------------------------------------------------------- the hutch plan
# Measured cubbies (inside height, mm). All are 380 wide x 240 deep.
#   top-left / top-middle  ~149     top-right  ~167.5     old Alexa bay  ~264.3
# Each stack: TPU pads (0.6) + modules stacked flush + TPU spacers on the top bumps.
# The top tier is 74 mm in all three top cubbies, so the black/sage colour line runs straight.
CAP_SQUEEZE = -0.3   # negative = clearance to the ceiling (solid TPU is far too stiff to squeeze)

PLAN = {
    # cubby: (cubby height, [(module height, face colour), ... bottom to top])
    "top_left":   (149.0, [(71, "sage"), (74, "black")]),
    "top_middle": (149.0, [(71, "sage"), (74, "black")]),
    "top_right":  (167.5, [(89.5, "sage"), (74, "black")]),
    "bay":        (264.3, [(128, "black"), (66, "sage"), (66, "black")]),
}


def stack_height(heights, p: P = None):
    p = p or P()
    return p.pad_out + sum(heights)


def cap_height(cubby_h, heights, p: P = None):
    """Spacer height above the topmost module's top surface, rounded to 0.5 mm."""
    return round((cubby_h - stack_height(heights, p) + CAP_SQUEEZE) * 2) / 2
