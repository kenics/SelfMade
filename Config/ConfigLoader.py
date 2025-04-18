import json
import os

class ConfigLoader:
    CONFIG_PATH = r"D:\SelfMade\Config\config.json"
    SECRETS_PATH = r"D:\EchoCodeForge\Config\secrets.json"

    def __init__(self):
        self.config = self._load_json(self.CONFIG_PATH, "設定ファイル(パラメータ)")
        self.secrets = self._load_json(self.SECRETS_PATH, "設定ファイル(セキュリティ)")

    def _load_json(self, path, description):
        if not os.path.exists(path):
            raise FileNotFoundError(f"{description}が見つかりません")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def get_secret(self, key, default=None):
        return self.secrets.get(key, default)
