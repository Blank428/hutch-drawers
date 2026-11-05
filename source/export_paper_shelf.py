"""Export the paper shelf STLs (print orientation) and build + verify its Bambu Studio projects."""
import json, os, subprocess, sys
import numpy as np, trimesh
import paper_shelf as ps
import paper_shelf_lite as L   # lighter version: windowed panels, slatted middle and top shelves, solid base

STL = "/home/claude/deliver/paper_shelf/stl"
REPO = "/home/claude/hutch-drawers"
RUN = "/tmp/claude-0/-home-claude/20827e43-d651-539b-a417-716e5ce789ba/scratchpad/bs/run.sh"
CFG = "/home/claude/hutch_drawers/bambu/cfg"
WORK = "/home/claude/hutch_drawers/bambu/work/ps"
os.makedirs(STL, exist_ok=True)


def save(m, name):
    mesh = m.to_mesh()
    trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts), process=False).export(f"{STL}/{name}.stl")
    return f"{STL}/{name}.stl"


panels = [save(L.panel_print(False), "paper_shelf_side_panel_left"), save(L.panel_print(True), "paper_shelf_side_panel_right")]
shelves = []
for name, (z0, ribs) in ps.SHELVES.items():
    l, r = ps.shelf_halves(z0, ribs) if name == "base" else L.shelf_halves(z0, ribs)
    shelves += [save(ps.shelf_print(l), f"paper_shelf_{name}_shelf_left_half"), save(ps.shelf_print(r), f"paper_shelf_{name}_shelf_right_half")]
pan, a, b = ps.fit_test()
fit = [save(ps._drop(pan.rotate([0, -90, 0])), "paper_shelf_fit_test_panel_slice"),
       save(ps.shelf_print(a), "paper_shelf_fit_test_shelf_a"), save(ps.shelf_print(b), "paper_shelf_fit_test_shelf_b")]

jobs = [("paper_shelf_fit", "projects/paper-shelf/paper_shelf_fit_test.3mf", "Paper shelf fit test", fit),
        ("paper_shelf_panels", "projects/paper-shelf/paper_shelf_side_panels_x2.3mf", "Paper shelf side panels, 2", panels),
        ("paper_shelf_shelves", "projects/paper-shelf/paper_shelf_shelf_halves_x6.3mf", "Paper shelf shelf halves, 6", shelves)]
man = json.load(open(f"{REPO}/manifest.json"))
for key, path, title, stls in jobs:
    out = f"{WORK}/{key}"; subprocess.run(["rm", "-rf", out]); os.makedirs(out)
    subprocess.run([RUN, "env", "LC_ALL=C.UTF-8", "/app/bin/bambu-studio", "--load-settings", f"{CFG}/machine.json;{CFG}/proc_std.json",
                    "--load-filaments", f"{CFG}/pla_black.json", "--arrange", "1", "--orient", "0", "--export-3mf", "project.3mf", "--outputdir", out] + stls,
                   capture_output=True, timeout=900)
    os.makedirs(os.path.dirname(f"{REPO}/{path}"), exist_ok=True)
    subprocess.run(["cp", f"{out}/project.3mf", f"{REPO}/{path}"])
    subprocess.run([RUN, "env", "LC_ALL=C.UTF-8", "/app/bin/bambu-studio", "--slice", "0", "--outputdir", f"{out}/s", f"{REPO}/{path}"], capture_output=True, timeout=900)
    r = json.load(open(f"{out}/s/result.json")); pl = r["sliced_plates"]
    g = sum(f["main_used_g"] for p in pl for f in p["filaments"]); t = sum(p["total_predication"] for p in pl)
    man[key] = dict(path=path, title=title, plates=len(pl), objects=sum(len(p["objects"]) for p in pl), grams=round(g, 1), minutes=round(t / 60, 1),
                    filament="black", warning=" ".join(p.get("warning_message", "") for p in pl).strip())
    print(f"{key:22s} rc {r['return_code']} plates {len(pl)}  {g:6.1f} g  {t/3600:5.2f} h  {man[key]['warning']}")
json.dump(man, open(f"{REPO}/manifest.json", "w"), indent=1)
