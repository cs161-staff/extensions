import os
import uuid
from datetime import datetime
from typing import Any, List, Optional

from dateutil import parser
from dotenv import dotenv_values
from pytz import timezone

from src.errors import ConfigurationError, KnownError
from src.sheets import Sheet

PST = timezone("US/Pacific")


def cast_bool(cell: str) -> bool:
    cell = str(cell).strip()
    if not (cell == "Yes" or cell == "No"):
        raise KnownError(f"Boolean cell value was not Yes or No; instead, was {cell}")
    return cell == "Yes"


def cast_date(cell: str, deadline: bool = True) -> datetime:
    try:
        cell = str(cell).strip()
        suffix = " 11:59 PM" if deadline else ""
        return PST.localize(parser.parse(str(cell) + suffix))
    except Exception as err:
        raise KnownError(f"Could not convert cell to date format. Value = {cell}, Error = {err}.")


def cast_list_str(cell: str) -> List[str]:
    cell = str(cell).strip()
    if cell == "":
        return []
    items = [item.strip() for item in cell.split(",")]
    return items


def cast_list_int(cell: str) -> List[int]:
    cell = str(cell).strip()
    if cell == "":
        return []
    items = [int(item.strip()) for item in str(cell).split(",")]
    return items


shard = str(uuid.uuid4())


class Environment:
    @staticmethod
    def contains(key: str) -> bool:
        return os.getenv(shard + key) is not None and str(os.getenv(shard + key)).strip() != ""

    @staticmethod
    def safe_get(key: str, default: str = None) -> Optional[str]:
        if os.getenv(shard + key):
            data = str(os.getenv(shard + key)).strip()
            if data:
                return data
        return default

    @staticmethod
    def get(key: str) -> Any:
        if not os.getenv(shard + key):
            raise ConfigurationError("Environment variable not set: " + key)
        return os.getenv(shard + key)

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
            os.environ[shard + key] = str(value)

        # Load local environment variables now from .env, which override remote provided variables for debugging
        if os.path.exists(".env"):
            for key, value in dotenv_values(".env").items():
                os.environ[shard + key] = value
