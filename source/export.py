"""Build the v2 print pack: print-ready STLs (already in print orientation, mm),
named with how many to print and in which colour."""
import sys
import os
import shutil
from collections import Counter
import numpy as np
import trimesh
sys.path.insert(0, '.')
from drawer_module import *
from drawer_module import _drop

PACK = "/home/claude/deliver/hutch_drawers_v2"


def save(m, path):
    mesh = m.to_mesh()
    assert m.status().name == 'NoError' and len(m.decompose()) == 1, path
    t = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False)
    assert t.is_watertight and t.is_winding_consistent and t.volume > 0, path
    b = t.bounds
    assert all(b[1] - b[0] <= 256), path
    t.export(path)
    return b[1] - b[0]


def fit_test_params():
    return P(H=74, D=105.6, grid_y=2, windows=False)


def build():
    shutil.rmtree(PACK, ignore_errors=True)
    a = f"{PACK}/1_fit_test_print_first"
    b = f"{PACK}/2_full_set"
    c = f"{PACK}/3_tpu_parts"
    for d in (a, b, c):
        os.makedirs(d)

    q = fit_test_params()
    save(frame_print(q), f"{a}/fit_frame_x1_black.stl")
    save(drawer_print(q), f"{a}/fit_drawer_x1_black.stl")
    save(faceplate_print(q), f"{a}/fit_faceplate_x2_one_black_one_sage.stl")
    save(_drop(latch(q, 1)), f"{a}/fit_latch_right_x1_black.stl")
    save(_drop(latch(q, -1)), f"{a}/fit_latch_left_x1_black.stl")
    save(_drop(label_tag(q)), f"{a}/fit_label_tag_x1_any_colour.stl")
    save(_drop(tpu_pad(q)), f"{a}/fit_foot_pad_x4_tpu.stl")
    save(_drop(tpu_cap(q, 3.0)), f"{a}/fit_top_spacer_3.0mm_x1_tpu.stl")

    # count modules and faceplate colours across the plan
    mods, faces = Counter(), Counter()
    bottoms, tops, caps = 0, 0, Counter()
    for cubby, (ch, stack) in PLAN.items():
        hs = [h for h, _ in stack]
        for h, col in stack:
            mods[h] += 2
            faces[(h, col)] += 2
        bottoms += 2
        caps[cap_height(ch, hs)] += 2 * 4
    for h, n in sorted(mods.items()):
        r = P(H=h)
        save(frame_print(r), f"{b}/{h}mm_frame_x{n}_black.stl")
        save(drawer_print(r), f"{b}/{h}mm_drawer_x{n}_black.stl")
        for col in ("black", "sage"):
            k = faces[(h, col)]
            if k:
                save(faceplate_print(r), f"{b}/{h}mm_faceplate_x{k}_{col}.stl")
    save(_drop(latch(P(), 1)), f"{b}/latch_right_x18_black.stl")
    save(_drop(latch(P(), -1)), f"{b}/latch_left_x18_black.stl")
    save(_drop(label_tag(P())), f"{b}/label_tag_x18_optional.stl")
    save(_drop(tpu_pad(P())), f"{c}/foot_pad_x{bottoms * 4}_tpu.stl")
    for h in (2.5, 3.0, 3.5, 4.0, 4.5):
        n = caps.get(h, 0)
        name = f"top_spacer_{h}mm_x{n}_tpu.stl" if n else f"top_spacer_{h}mm_spare_size.stl"
        save(_drop(tpu_cap(P(), h)), f"{c}/{name}")
    return mods, faces, caps, bottoms


if __name__ == "__main__":
    mods, faces, caps, bottoms = build()
    print("modules", dict(mods)); print("faces", dict(faces)); print("caps", dict(caps), "bottom modules", bottoms)
    for root, _, files in sorted(os.walk(PACK)):
        for f in sorted(files):
            print(os.path.relpath(os.path.join(root, f), PACK))
