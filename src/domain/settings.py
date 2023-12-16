import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SETTINGS_DIR = BASE_DIR / 'settings.json'


class Settings:
    """Settings for the mailer."""

    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_USERNAME: str
    EMAIL_PASSWORD: str
    WAIT_TIME: int

    def __init__(self):
        self._settings = {}
        self.load()

    def load(self):
        """Load settings from a file."""
        SETTINGS_DIR.touch(exist_ok=True)
        with open(SETTINGS_DIR) as f:
            read = f.read()
            self._settings = {}
            if read:
                self._settings = json.loads(read)

    def save(self):
        """Save settings to a file."""
        with open(SETTINGS_DIR, 'w') as f:
            json.dump(self._settings, f)

    def __getattr__(self, name):
        return self._settings.get(name, None)

    def __setattr__(self, name, value: str | int):
        if name == '_settings':
            super().__setattr__(name, value)
        else:
            self._settings[name] = value
            self.save()


settings = Settings()
