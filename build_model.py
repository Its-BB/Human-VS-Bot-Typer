import shutil
from pathlib import Path

from timing_model import MODEL_PATH, save_model

if __name__ == "__main__":
    b = save_model()
    api_dst = Path(__file__).resolve().parent / "api" / "models"
    api_dst.mkdir(parents=True, exist_ok=True)
    shutil.copy(MODEL_PATH, api_dst / "bundle.joblib")
    print(f"saved model cv={b.cv_acc}")