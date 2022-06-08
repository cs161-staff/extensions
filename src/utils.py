import os
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

    # Default empty cells to a "No" boolean.
    if cell == "":
        cell = "No"

    if not (cell in ["Yes", "No", "TRUE", "FALSE"]):
        raise KnownError(f"Boolean cell value was not Yes or No; instead, was {cell}")
    return cell == "Yes" or cell == "TRUE"


def cast_date(cell: str, deadline: bool = True, optional: bool = False) -> Optional[datetime]:
    try:
        if optional and (cell is None or str(cell).strip() == ""):
            return None
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


PREFIX = "cs161extensions_"


class Environment:
    @staticmethod
    def clear():
        keys = os.environ.keys()
        for key in keys:
            if key.startswith(PREFIX):
                del os.environ[key]

    @staticmethod
    def contains(key: str) -> bool:
        return os.getenv(PREFIX + key) is not None and str(os.getenv(PREFIX + key)).strip() != ""

    @staticmethod
    def safe_get(key: str, default: str = None) -> Optional[str]:
        if os.getenv(PREFIX + key):
            data = str(os.getenv(PREFIX + key)).strip()
            if data:
                return data
        return default

    @staticmethod
    def get(key: str) -> Any:
        if not os.getenv(PREFIX + key):
            raise ConfigurationError("Environment variable not set: " + key)
        return os.getenv(PREFIX + key)

    @staticmethod
    def get_auto_approve_threshold() -> int:
        return int(Environment.get("AUTO_APPROVE_THRESHOLD"))

    @staticmethod
    def get_auto_approve_threshold_dsp() -> int:
        return int(Environment.get("AUTO_APPROVE_THRESHOLD_DSP"))

    @staticmethod
    def get_max_total_requested_extensions_threshold() -> int:
        # If this number is -1, then assume this flag is disabled.
        # If this number is 0, then reject all extensions.
        # If this number is > 0, then reject extensions if the total number of extensions requested exceeds this number.
        return int(Environment.safe_get("MAX_TOTAL_REQUESTED_EXTENSIONS_THRESHOLD", default=-1))

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
            os.environ[PREFIX + key] = str(value)

        # Load local environment variables now from .env, which override remote provided variables for debugging
        if os.path.exists(".env-pytest"):
            for key, value in dotenv_values(".env-pytest").items():
                if key == "APP_MASTER_SECRET":
                    os.environ[key] = value
                else:
                    os.environ[PREFIX + key] = value


def truncate(s, amount=300):
    s = str(s)
    if len(s) > amount:
        s = s[:amount] + "...see GCP for entire log."
    return s
