import os
from typing import Any
from src.errors import ConfigurationError
from src.sheets import Sheet


class Environment:
    @staticmethod
    def get(key: str) -> Any:
        if not os.getenv(key):
            raise ConfigurationError("Environment variable not set.")
        return os.getenv(key)
        
    @staticmethod
    def get_auto_approve_threshold() -> int:
        return int(Environment.get("AUTO_APPROVE_THRESHOLD"))

    @staticmethod
    def get_auto_approve_threshold_dsp() -> int:
        return int(Environment.get("AUTO_APPROVE_THRESHOLD_DSP"))

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
            if not value:
                raise ConfigurationError(f"Environment variable {key} is not defined. Please define in sheet.")
            os.environ[key] = str(value)
