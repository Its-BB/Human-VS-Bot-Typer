import shutil
from pathlib import Path

from timing_model import MODEL_PATH, save_model

ROOT = Path(__file__).resolve().parent
API = ROOT / "api"

if __name__ == "__main__":
    b = save_model()
    dst = API / "models"
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(MODEL_PATH, dst / "bundle.joblib")
    pub = API / "public"
    if pub.exists():
        shutil.rmtree(pub)
    shutil.copytree(ROOT / "public", pub)
    print(f"saved model cv={b.cv_acc}")
