import pandas as pd

from engine.detection_engine import DetectionEngine
from utils.feature_builder import FeatureBuilder
from utils.config_loader import ConfigLoader
from utils.report_generator import ReportGenerator


CONFIG_PATH = "config/config.yaml"
INPUT_FILE = "benchmark/pipeline_metrics.csv"
OUTPUT_FILE = "output/anomaly_report.md"


def main():

    print("Loading config...")

    config = ConfigLoader.load(CONFIG_PATH)

    print("Loading pipeline metrics...")

    df = pd.read_csv(INPUT_FILE)

    print("Building features...")

    df = FeatureBuilder.build(df)

    print("Running anomaly detection...")

    engine = DetectionEngine(config)

    anomalies = engine.run(df)

    print(f"Detected anomalies: {len(anomalies)}")

    print("Generating report...")

    ReportGenerator.generate(
        anomalies,
        OUTPUT_FILE
    )

    print("Done.")


if __name__ == "__main__":
    main()