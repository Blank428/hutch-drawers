"""Flatten Bambu Studio system presets (resolve the `inherits` chain) and apply overrides."""
import json, os, glob
BASE = os.path.expanduser("~/.local/share/flatpak/app/com.bambulab.BambuStudio/x86_64/stable/active/files/share/BambuStudio/profiles/BBL")
_index = {}
for kind in ("machine", "process", "filament"):
    for f in glob.glob(f"{BASE}/{kind}/**/*.json", recursive=True):
        try: d = json.load(open(f))
        except Exception: continue
        if "name" in d: _index[(kind, d["name"])] = d

def flat(kind, name):
    d = _index[(kind, name)]
    if d.get("inherits"):
        out = flat(kind, d["inherits"])
    else:
        out = {}
    out.update({k: v for k, v in d.items() if k not in ("inherits",)})
    return out

def write(kind, name, path, **over):
    d = flat(kind, name)
    d.update(over)
    d["from"] = "system" if not over else "User"
    if over:
        d["inherits"] = name; d["name"] = os.path.splitext(os.path.basename(path))[0]
    json.dump(d, open(path, "w"), indent=1)
    return path
