"""Label tag v3: press-fit tag for the faceplate label slot (50 x 14 x 1 mm recess).
Base 0.6 mm in the front's colour; text is added on top (0.4 mm, other colour) by the
label maker page. Four small ribs on the long edges give a 0.1 mm press fit, and a 0.35 mm
chamfer on the bottom edge gets it past first-layer squish at the slot mouth."""
import sys
sys.path.insert(0, '.')
from drawer_module import P, rrect, Manifold, CrossSection, OpType, _drop

CLEAR = 0.15        # per side, outline to slot wall
RIB_R = 0.6
RIB_OUT = 0.25      # rib stands this far past the outline: 0.1 mm interference
CH = 0.35           # bottom edge chamfer
BASE_T = 0.6


def tag_base(p: P, t=BASE_T, ribs=True):
    w, h = p.label_w - 2 * CLEAR, p.label_h - 2 * CLEAR
    r = 1.5 - CLEAR
    outline = rrect(w, h, r)
    bottom = Manifold.extrude(rrect(w - 2 * CH, h - 2 * CH, max(r - CH, 0.2)), 0.01)
    upper = Manifold.extrude(outline, t - CH).translate((0, 0, CH))
    m = Manifold.batch_hull([bottom, Manifold.extrude(outline, 0.01).translate((0, 0, CH))]) + upper
    if ribs:
        for x in (-w / 4, w / 4):
            for sy in (-1, 1):
                y = sy * (h / 2 + RIB_OUT - RIB_R)
                m = m + Manifold.cylinder(t - CH - 0.05, RIB_R).translate((x, y, CH + 0.05))
    return m
