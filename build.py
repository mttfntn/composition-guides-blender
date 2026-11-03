"""Package the add-on as composition_guides.zip (installable on Blender 3.6+ and as a 4.2+ extension)."""

import os
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "composition_guides")
OUT = os.path.join(ROOT, "composition_guides.zip")

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
    for name in sorted(os.listdir(SRC)):
        path = os.path.join(SRC, name)
        if os.path.isfile(path) and not name.endswith(".pyc"):
            zf.write(path, "composition_guides/" + name)
print("Wrote", OUT)
