from dataclasses import dataclass
from typing import Any


@dataclass
class Status:
    status: bool
    return_value: Any


def ok(return_value: Any) -> Status:
    return Status(True, return_value)


def error(error_str: str) -> Status:
    return Status(False, error_str)
