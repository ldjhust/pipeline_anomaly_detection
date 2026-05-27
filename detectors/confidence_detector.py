import pandas as pd

from detectors.base_detector import BaseDetector


class ConfidenceDriftDetector(BaseDetector):

    anomaly_type = "confidence_drift"
    metric_name = "avg_confidence"

    def detect(self, df: pd.DataFrame):

        window_size = self.config.get("window_size", 10)
        std_threshold = self.config.get("std_threshold", 2.5)

        sorted_df = df.sort_values("start_time").copy()

        sorted_df["rolling_mean"] = (
            sorted_df[self.metric_name]
            .rolling(window=window_size)
            .mean()
        )

        sorted_df["rolling_std"] = (
            sorted_df[self.metric_name]
            .rolling(window=window_size)
            .std()
        )

        results = []

        for _, row in sorted_df.iterrows():

            if pd.isna(row["rolling_mean"]):
                continue

            mean = row["rolling_mean"]
            std = row["rolling_std"]
            value = row[self.metric_name]

            upper = mean + std_threshold * std
            lower = mean - std_threshold * std

            if lower <= value <= upper:
                continue

            deviation_score = abs(value - mean)

            severity = (
                "critical"
                if deviation_score > std_threshold * std * 1.5
                else "warning"
            )

            results.append({
                "batch_id": row["batch_id"],
                "anomaly_type": self.anomaly_type,
                "metric_name": self.metric_name,
                "detection_method": "sliding_window",
                "trigger_condition":
                    f"|x - mean| > {std_threshold}σ",
                "actual_value": round(value, 4),
                "expected_range":
                    f"[{round(lower, 4)}, {round(upper, 4)}]",
                "deviation_score": round(deviation_score, 4),
                "severity": severity
            })

        return results