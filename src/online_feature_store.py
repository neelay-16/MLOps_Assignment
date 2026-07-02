import os
import redis
from src.logger import get_logger
from src.custom_exception import CustomException
import sys
import json
logger = get_logger(__name__)

class OnlineFeatureStore:
    def __init__(self):
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT_NUMBER", 6379))

        try:
            self.client = redis.StrictRedis(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True,
                socket_timeout=5
            )
            self.client.ping()
            logger.info(f"✅ Connected to Redis at {redis_host}:{redis_port}")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise CustomException("Redis connection failed", sys.exc_info())

    def store_patient_features(self, patient_id: str, features: dict):
        """Store latest features for a patient (used during data ingestion)"""
        try:
            key = f"patient:{patient_id}:features"
            self.client.set(key, json.dumps(features))
            # Optional: Set expiration (e.g., 30 days)
            self.client.expire(key, 30 * 24 * 60 * 60)
            logger.info(f"Stored features for patient {patient_id}")
        except Exception as e:
            logger.error(f"Failed to store patient features: {e}")

    def get_patient_features(self, patient_id: str):
        """Get latest features for real-time prediction.
        Tries multiple key formats for safety.
        """
        try:
            patient_id = str(patient_id).strip()
            
            # Try both possible key formats
            possible_keys = [
                f"patient:{patient_id}:features",   # New/correct format
                f"patient:{patient_id}",            # Old format (fallback)
            ]
            
            for key in possible_keys:
                data = self.client.get(key)
                if data:
                    logger.info(f"Found data using key: {key}")
                    return json.loads(data)
            
            logger.warning(f"No features found for patient_id: {patient_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error in get_patient_features: {e}")
            return None

    def get_all_patient_ids(self):
        """Get all patients currently in online store"""
        try:
            keys = self.client.keys("patient:*:features")
            patient_ids = []
            for key in keys:
                pid = key.split(":")[1]
                patient_ids.append(pid)
            return patient_ids
        except Exception as e:
            logger.error(f"Error getting patient IDs: {e}")
            return []