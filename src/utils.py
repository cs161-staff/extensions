import os
from typing import Any, Optional
from src.errors import ConfigurationError
from src.sheets import Sheet


class Environment:
    @staticmethod
    def contains(key: str) -> bool:
        return os.getenv(key) is not None and str(os.getenv(key)).strip() != ""

    @staticmethod
    def safe_get(key: str, default: str = None) -> Optional[str]:
        if os.getenv(key):
            data = str(os.getenv(key)).strip()
            if data:
                return data
        return default

    @staticmethod
    def get(key: str) -> Any:
        if not os.getenv(key):
            raise ConfigurationError("Environment variable not set: " + key)
        return os.getenv(key)

    @staticmethod
    def get_auto_approve_threshold() -> int:
        return int(Environment.get("AUTO_APPROVE_THRESHOLD"))

    @staticmethod
    def get_auto_approve_threshold_dsp() -> int:
        return int(Environment.get("AUTO_APPROVE_THRESHOLD_DSP"))

    @staticmethod
    def get_auto_approve_assignment_threshold() -> int:
        return int(Environment.get("AUTO_APPROVE_ASSIGNMENT_THRESHOLD"))

    @staticmethod
    def configure_env_vars(sheet: Sheet):
        """
        Reads environment variables from the "Environment Variables" sheet, and stores them into this process's
        environment variables for downstream use. Expects two columns: a "key" column, and a "value"
        """
        records = sheet.get_all_records()
        for record in records:
            key = record.get("key")
            value = record.get("value")
            if not key:
                continue
            os.environ[key] = str(value)
