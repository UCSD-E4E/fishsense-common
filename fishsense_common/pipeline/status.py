from typing import Any


class Status:
    def __init__(self, status: bool, return_value: Any):
        self.status = status
        self.return_value = return_value

    def __bool__(self) -> bool:
        return self.status

    def __repr__(self) -> str:
        return f"Status(status={self.status}, return_value={self.return_value})"

    def __str__(self) -> str:
        return f"Status: {self.status}, Return Value: {self.return_value}"


def ok(return_value: Any) -> Status:
    return Status(True, return_value)


def error(error_str: str) -> Status:
    return Status(False, error_str)
