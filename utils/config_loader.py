import yaml


class ConfigLoader:

    @staticmethod
    def load(config_path: str):

        with open(config_path, "r") as file:
            return yaml.safe_load(file)