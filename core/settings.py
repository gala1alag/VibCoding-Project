import json
import os

_SETTINGS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "settings.json")

_DEFAULTS = {
    "theme": "dark",
    "default_editor": "",
    "db_path": os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "devhub.db"),
}

class Settings:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._data = dict(_DEFAULTS)
            cls._instance._load()
        return cls._instance

    def _load(self):
        if os.path.exists(_SETTINGS_PATH):
            try:
                with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                    self._data.update(json.load(f))
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: could not load settings: {e}")

    def save(self):
        os.makedirs(os.path.dirname(_SETTINGS_PATH), exist_ok=True)
        with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key: str):
        return self._data.get(key)

    def set(self, key: str, value):
        self._data[key] = value
        self.save()
