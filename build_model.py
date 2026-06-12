from timing_model import save_model

if __name__ == "__main__":
    b = save_model()
    print(f"saved model cv={b.cv_acc}")
