from pathlib import Path
import yaml

config_path = Path(__file__).parent / 'config.yaml'


def load_config(path=config_path):
    with open(path, 'r') as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
    return config


config = load_config()
