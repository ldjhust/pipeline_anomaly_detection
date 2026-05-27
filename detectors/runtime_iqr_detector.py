import pandas as pd

from detectors.base_detector import BaseDetector


class RuntimeIQRDetector(BaseDetector):

    anomaly_type = "runtime_anomaly"
    metric_name = "duration_seconds"

    def detect(self, df: pd.DataFrame):

        metric_series = df[self.metric_name]

        q1 = metric_series.quantile(0.25)
        q3 = metric_series.quantile(0.75)

        iqr = q3 - q1

        multiplier = self.config.get("iqr_multiplier", 1.5)

        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr

        anomalies = df[
            (metric_series < lower)
            | (metric_series > upper)
        ].copy()

        if anomalies.empty:
            return []

        results = []

        for _, row in anomalies.iterrows():

            actual_value = row[self.metric_name]

            deviation_score = max(
                abs(actual_value - lower),
                abs(actual_value - upper)
            )

            severity = (
                "critical"
                if actual_value > upper * 1.5
                else "warning"
            )

            results.append({
                "batch_id": row["batch_id"],
                "anomaly_type": self.anomaly_type,
                "metric_name": self.metric_name,
                "detection_method": "iqr",
                "trigger_condition":
                    f"{self.metric_name} > {round(upper, 4)}",
                "actual_value": round(actual_value, 4),
                "expected_range":
                    f"[{round(lower, 4)}, {round(upper, 4)}]",
                "deviation_score": round(deviation_score, 4),
                "severity": severity
            })

        return results