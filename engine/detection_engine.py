from detectors.runtime_iqr_detector import RuntimeIQRDetector
from detectors.volume_detector import VolumeDetector
from detectors.confidence_detector import ConfidenceDriftDetector


class DetectionEngine:

    def __init__(self, config):

        self.config = config
        self.detectors = []

        self._register_detectors()

    def _register_detectors(self):

        if self.config["runtime"]["enabled"]:
            self.detectors.append(
                RuntimeIQRDetector(
                    self.config["runtime"]
                )
            )

        if self.config["volume"]["enabled"]:
            self.detectors.append(
                VolumeDetector(
                    self.config["volume"]
                )
            )

        if self.config["confidence"]["enabled"]:
            self.detectors.append(
                ConfidenceDriftDetector(
                    self.config["confidence"]
                )
            )

    def run(self, df):

        all_anomalies = []

        for detector in self.detectors:

            detector_results = detector.detect(df)

            all_anomalies.extend(detector_results)

        return all_anomalies