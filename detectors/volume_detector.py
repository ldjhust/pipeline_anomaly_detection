import pandas as pd

from detectors.base_detector import BaseDetector


class VolumeDetector(BaseDetector):

    anomaly_type = "volume_anomaly"

    def detect(self, df: pd.DataFrame):

        results = []

        metric_series = df["output_count"]

        q1 = metric_series.quantile(0.25)
        q3 = metric_series.quantile(0.75)

        iqr = q3 - q1

        multiplier = self.config.get(
            "iqr_multiplier",
            1.5
        )

        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr

        ratio_threshold = self.config.get(
            "min_ratio_threshold",
            0.5
        )

        for _, row in df.iterrows():

            batch_id = row["batch_id"]

            output_count = row["output_count"]
            output_ratio = row["output_ratio"]

            # -------------------------------------------------
            # output_count anomaly
            # -------------------------------------------------

            if output_count < lower:

                deviation_score = abs(
                    output_count - lower
                )

                severity = (
                    "critical"
                    if output_count < lower * 0.5
                    else "warning"
                )

                results.append({
                    "batch_id": batch_id,
                    "anomaly_type": self.anomaly_type,
                    "metric_name": "output_count",
                    "detection_method": "iqr",
                    "trigger_condition":
                        f"output_count < {round(lower, 4)}",
                    "actual_value": round(output_count, 4),
                    "expected_range":
                        f"[{round(lower, 4)}, "
                        f"{round(upper, 4)}]",
                    "deviation_score":
                        round(deviation_score, 4),
                    "severity": severity
                })

            # -------------------------------------------------
            # output_ratio anomaly
            # -------------------------------------------------

            if output_ratio < ratio_threshold:

                deviation_score = abs(
                    output_ratio - ratio_threshold
                )

                severity = (
                    "critical"
                    if output_ratio < ratio_threshold * 0.5
                    else "warning"
                )

                results.append({
                    "batch_id": batch_id,
                    "anomaly_type": self.anomaly_type,
                    "metric_name": "output_ratio",
                    "detection_method": "threshold",
                    "trigger_condition":
                        f"output_ratio < {ratio_threshold}",
                    "actual_value": round(output_ratio, 4),
                    "expected_range":
                        f"[{ratio_threshold}, +inf]",
                    "deviation_score":
                        round(deviation_score, 4),
                    "severity": severity
                })

        return results