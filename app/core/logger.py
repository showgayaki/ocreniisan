import json
from pathlib import Path
from logging import config


def load_looger() -> None:
    # log設定の読み込み
    app_dir = Path(__file__).parents[1].resolve()
    log_config = Path.joinpath(app_dir, 'log', 'config.json')

    with open(log_config) as f:
        config.dictConfig(json.load(f))
