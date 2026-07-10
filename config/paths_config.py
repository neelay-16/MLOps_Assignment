import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# FORCE the path to go directly inside the models folder safely
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "artifacts", "models")

RAW_DIR = os.path.join(BASE_DIR, "artifacts", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "artifacts", "processed")

TRAIN_PATH = os.path.join(RAW_DIR, "heart_disease_train.csv")
TEST_PATH = os.path.join(RAW_DIR, "heart_disease_test.csv")
