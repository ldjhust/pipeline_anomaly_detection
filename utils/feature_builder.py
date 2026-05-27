import pandas as pd


class FeatureBuilder:

    @staticmethod
    def build(df: pd.DataFrame):

        df = df.copy()

        df["start_time"] = pd.to_datetime(df["start_time"])
        df["end_time"] = pd.to_datetime(df["end_time"])

        df["duration_seconds"] = (
            df["end_time"] - df["start_time"]
        ).dt.total_seconds()

        df["output_ratio"] = (
            df["output_count"]
            / df["input_count"]
        )

        return df