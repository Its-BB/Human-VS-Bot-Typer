import shutil
from pathlib import Path

from timing_model import MODEL_PATH, save_model

ROOT = Path(__file__).resolve().parent
API = ROOT / "api"
PUBLIC = ROOT / "public"

ASSETS = ("index.html", "app.js", "style.css")
TYPES = {
    "index.html": "text/html; charset=utf-8",
    "app.js": "application/javascript; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
}


def bundle_assets() -> None:
    lines = ['TYPES = ' + repr(TYPES), "FILES = {"]
    for name in ASSETS:
        text = (PUBLIC / name).read_text(encoding="utf-8")
        lines.append(f"    {name!r}: {text!r},")
    lines.append("}")
    (API / "_assets.py").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    b = save_model()
    dst = API / "models"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(MODEL_PATH, dst / "bundle.joblib")
    bundle_assets()
    print(f"saved model cv={b.cv_acc}")
