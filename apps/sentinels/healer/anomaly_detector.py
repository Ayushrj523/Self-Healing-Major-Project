"""
SENTINELS v2.0 — Isolation Forest Anomaly Detector
Trains on baseline metrics, scores incoming telemetry.
Model: IsolationForest(contamination=0.02, n_estimators=200, max_samples=256)
"""
import logging, time, json
from typing import Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger("sentinels.anomaly")

# Feature vector: [cpu_percent, mem_percent, restart_count, error_rate, latency_p99, request_rate]
FEATURE_NAMES = [
    "cpu_percent", "mem_percent", "restart_count",
    "error_rate_5xx", "latency_p99_ms", "request_rate_rps"
]

class AnomalyDetector:
    """Isolation Forest based anomaly detection with online retraining."""

    def __init__(self, contamination: float = 0.02, n_estimators: int = 200,
                 max_samples: int = 256, threshold: float = -0.30):
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.threshold = threshold  # Scores below this = anomaly
        self.model: Optional[IsolationForest] = None
        self.scaler = StandardScaler()
        self.baseline_data: list = []
        self.is_trained = False
        self.training_samples = 0
        self.last_retrain_time = 0.0
        self.retrain_interval = 1800  # 30 minutes
        self.min_baseline_samples = 20  # Minimum samples before training

    def add_baseline_sample(self, features: dict) -> None:
        """Add a baseline sample during the observation period."""
        vector = self._dict_to_vector(features)
        if vector is not None:
            self.baseline_data.append(vector)
            logger.debug(f"Baseline sample added: {len(self.baseline_data)} total")

    def train(self, force: bool = False) -> bool:
        """Train or retrain the Isolation Forest model."""
        if len(self.baseline_data) < self.min_baseline_samples and not force:
            logger.warning(f"Not enough baseline data: {len(self.baseline_data)}/{self.min_baseline_samples}")
            return False

        X = np.array(self.baseline_data)
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        self.model = IsolationForest(
            contamination=self.contamination,
            n_estimators=self.n_estimators,
            max_samples=min(self.max_samples, len(X_scaled)),
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_scaled)
        self.is_trained = True
        self.training_samples = len(X_scaled)
        self.last_retrain_time = time.time()

        logger.info(f"Isolation Forest trained on {self.training_samples} samples | "
                     f"contamination={self.contamination}, n_estimators={self.n_estimators}")
        return True

    def score(self, features: dict) -> dict:
        """Score a feature vector. Returns anomaly_score + verdict."""
        if not self.is_trained or self.model is None:
            return {
                "anomaly_score": 0.0,
                "is_anomaly": False,
                "confidence": 0.0,
                "reason": "Model not trained yet — still in baseline observation period",
                "features": features
            }

        vector = self._dict_to_vector(features)
        if vector is None:
            return {"anomaly_score": 0.0, "is_anomaly": False, "confidence": 0.0,
                    "reason": "Invalid feature vector", "features": features}

        X = np.array([vector])
        X_scaled = self.scaler.transform(X)

        # decision_function returns negative for anomalies
        anomaly_score = float(self.model.decision_function(X_scaled)[0])
        prediction = int(self.model.predict(X_scaled)[0])  # -1 = anomaly, 1 = normal

        is_anomaly = anomaly_score < self.threshold
        confidence = min(1.0, abs(anomaly_score - self.threshold) / abs(self.threshold))

        # Determine primary anomaly type
        anomaly_type = self._classify_anomaly_type(features) if is_anomaly else "none"

        # Add to baseline for incremental learning
        if not is_anomaly:
            self.baseline_data.append(vector)
            # Periodic retrain
            if time.time() - self.last_retrain_time > self.retrain_interval:
                self.train(force=True)

        result = {
            "anomaly_score": round(anomaly_score, 4),
            "is_anomaly": is_anomaly,
            "confidence": round(confidence, 4),
            "threshold": self.threshold,
            "anomaly_type": anomaly_type,
            "prediction": prediction,
            "reason": self._build_reason(features, anomaly_score, anomaly_type),
            "features": features,
            "model_info": {
                "training_samples": self.training_samples,
                "contamination": self.contamination,
                "n_estimators": self.n_estimators
            }
        }

        logger.info(f"Anomaly score: {anomaly_score:.4f} | "
                     f"{'ANOMALY' if is_anomaly else 'NORMAL'} | "
                     f"type={anomaly_type} | confidence={confidence:.2f}")
        return result

    def _dict_to_vector(self, features: dict) -> Optional[list]:
        """Convert feature dict to ordered vector."""
        try:
            return [float(features.get(f, 0.0)) for f in FEATURE_NAMES]
        except (ValueError, TypeError):
            logger.error(f"Invalid features: {features}")
            return None

    def _classify_anomaly_type(self, features: dict) -> str:
        """Determine primary anomaly type based on which feature is most deviant."""
        thresholds = {
            "high_cpu": ("cpu_percent", 80.0),
            "high_memory": ("mem_percent", 85.0),
            "crash_loop": ("restart_count", 3.0),
            "high_error_rate": ("error_rate_5xx", 5.0),
            "high_latency": ("latency_p99_ms", 2000.0),
            "traffic_spike": ("request_rate_rps", 500.0),
        }
        for anomaly_name, (feature, threshold) in thresholds.items():
            if features.get(feature, 0) > threshold:
                return anomaly_name
        return "unknown_anomaly"

    def _build_reason(self, features: dict, score: float, anomaly_type: str) -> str:
        """Build human-readable explanation (Law 1: Explainability)."""
        if anomaly_type == "none":
            return f"Normal operation. Score {score:.4f} above threshold {self.threshold}"

        reasons = {
            "high_cpu": f"CPU at {features.get('cpu_percent', 0):.1f}% — exceeds safe threshold",
            "high_memory": f"Memory at {features.get('mem_percent', 0):.1f}% — risk of OOMKill",
            "crash_loop": f"Pod restarted {int(features.get('restart_count', 0))} times — possible crash loop",
            "high_error_rate": f"5xx error rate at {features.get('error_rate_5xx', 0):.1f}% — service degradation",
            "high_latency": f"P99 latency at {features.get('latency_p99_ms', 0):.0f}ms — slow response times",
            "traffic_spike": f"Request rate at {features.get('request_rate_rps', 0):.0f} RPS — potential DDoS",
        }
        reason = reasons.get(anomaly_type, f"Anomaly type: {anomaly_type}")
        return f"{reason}. IF score {score:.4f} below threshold {self.threshold}, " \
               f"confirming anomalous behavior detected by Isolation Forest model."

    def get_status(self) -> dict:
        return {
            "is_trained": self.is_trained,
            "training_samples": self.training_samples,
            "baseline_collected": len(self.baseline_data),
            "min_required": self.min_baseline_samples,
            "threshold": self.threshold,
            "contamination": self.contamination,
            "last_retrain": self.last_retrain_time,
        }
