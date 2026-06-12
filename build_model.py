import shutil
from pathlib import Path

from timing_model import MODEL_PATH, save_model

API_MODELS = Path(__file__).resolve().parent / "api" / "models"

if __name__ == "__main__":
    b = save_model()
    API_MODELS.mkdir(parents=True, exist_ok=True)
    shutil.copy(MODEL_PATH, API_MODELS / "bundle.joblib")
    print(f"saved model cv={b.cv_acc}")
