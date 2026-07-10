import pandas as pd
import numpy as np
import pickle
import os
import sys
from src.logger import get_logger
from src.custom_exception import CustomException
from src.online_feature_store import OnlineFeatureStore

logger = get_logger(__name__)


class OnlineHeartDiseasePrediction:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.online_store = OnlineFeatureStore()
        self.load_models()

    def load_models(self):
        """Load models from artifacts/ folder"""
        logger.info("Loading models for Online Prediction...")

        model_dir = "artifacts/models"

        # Logistic Regression
        try:
            lr_path = os.path.join(model_dir, "logistic_regression.pkl")
            if os.path.exists(lr_path):
                with open(lr_path, "rb") as f:
                    self.models["LogisticRegression"] = pickle.load(f)
                logger.info("✓ Logistic Regression loaded")
        except Exception as e:
            logger.error(f"Failed to load Logistic Regression: {e}")

        # Random Forest
        try:
            rf_path = os.path.join(model_dir, "random_forest.pkl")
            if os.path.exists(rf_path):
                with open(rf_path, "rb") as f:
                    self.models["RandomForest"] = pickle.load(f)
                logger.info("✓ Random Forest loaded")
        except Exception as e:
            logger.error(f"Failed to load Random Forest: {e}")

        # Keras Neural Network
        try:
            keras_path = os.path.join(model_dir, "keras_neural_network.keras")
            scaler_path = os.path.join(model_dir, "keras_scaler.pkl")

            if os.path.exists(keras_path) and os.path.exists(scaler_path):
                from tensorflow.keras.models import load_model
                self.models["KerasNN"] = load_model(keras_path)
                with open(scaler_path, "rb") as f:
                    self.scalers["KerasNN"] = pickle.load(f)
                logger.info("✓ Keras Neural Network loaded")
        except Exception as e:
            logger.error(f"Failed to load Keras model: {e}")

        if not self.models:
            logger.error("❌ No models loaded! Check artifacts/ folder.")
        else:
            logger.info(f"Successfully loaded {len(self.models)} model(s)")

    def predict_online(self, patient_id: str = None, feature_dict: dict = None):
        try:
            if not self.models:
                raise Exception("No models loaded. Check artifacts/ folder.")

            # ====================== Define Expected Features ======================
            expected_features = [
                'age', 'sex', 'cp', 'trestbps', 'chol', 'fbs',
                'restecg', 'thalach', 'exang', 'oldpeak', 'slope',
                'ca', 'thal'
            ]

            # ====================== Get Features ======================
            if patient_id:
                features = self.online_store.get_patient_features(patient_id)
                if not features:
                    raise ValueError(f"No features found for patient_id: {patient_id}")
                
                # Filter only the 13 features the model expects
                filtered_features = {k: features.get(k, 0) for k in expected_features}
                input_df = pd.DataFrame([filtered_features])[expected_features]

            elif feature_dict:
                # Filter only the 13 features the model expects
                filtered_features = {k: feature_dict.get(k, 0) for k in expected_features}
                input_df = pd.DataFrame([filtered_features])[expected_features]
            else:
                raise ValueError("Provide either patient_id or feature_dict")

            # ====================== Make Predictions ======================
            results = {}
            probabilities = []

            for model_name, loaded_object in self.models.items():
                
                # Handle both old format (dict) and new format (direct model)
                if isinstance(loaded_object, dict):
                    model = loaded_object.get('model', loaded_object)
                    scaler = loaded_object.get('scaler', None)
                else:
                    model = loaded_object
                    scaler = self.scalers.get(model_name)

                # ====================== Prediction Logic ======================
                # 1. Prepare scaled input if the model requires a scaler
                if scaler:
                    scaled_arr = scaler.transform(input_df)
                    # Convert to DataFrame to pass the correct feature names to scikit-learn
                    scaled_input = pd.DataFrame(scaled_arr, columns=input_df.columns, index=input_df.index)
                else:
                    scaled_input = input_df

                # 2. Run inference on the correct data matrix format
                if model_name == "KerasNN":
                    prob = float(model.predict(scaled_input, verbose=0)[0][0])
                elif model_name == "LogisticRegression":
                    # FIX: Pass scaled features so probability doesn't get distorted to 1.0
                    prob = float(model.predict_proba(scaled_input)[0][1])
                else:
                    # Random Forest runs on raw, unscaled features as done in your notebook
                    prob = float(model.predict_proba(input_df)[0][1])

                pred = 1 if prob > 0.5 else 0
                results[model_name] = {
                    "prediction": pred,
                    "probability": round(prob, 4)
                }
                probabilities.append(prob)

            # ====================== Final Verdict ======================
            if len(probabilities) == 0:
                raise Exception("No predictions were made.")

            vote_count = sum(r["prediction"] for r in results.values())
            final_prediction = 1 if vote_count >= 2 else 0
            avg_probability = round(sum(probabilities) / len(probabilities), 4)

            final_status = "HIGH RISK - Heart Disease" if final_prediction == 1 else "LOW RISK - No Heart Disease"

            # Print nice output
            print("\n" + "="*85)
            print(f"❤️ HEART DISEASE PREDICTION | Patient ID: {patient_id or 'Manual Input'}")
            print("="*85)
            for name, res in results.items():
                status = "🟥 HIGH RISK" if res["prediction"] == 1 else "🟢 LOW RISK"
                print(f"{name:20} → {status:15} | Probability: {res['probability']:.4f}")
            print("-"*85)
            print(f"{'FINAL VERDICT':20} → {final_status}")
            print(f"{'Average Probability':20} → {avg_probability:.4f}")
            print("="*85 + "\n")

            return {
                "final_prediction": final_prediction,
                "final_status": final_status,
                "average_probability": avg_probability,
                "individual_predictions": results
            }

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            raise CustomException(str(e), sys.exc_info())
