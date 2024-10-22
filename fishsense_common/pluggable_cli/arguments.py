from inspect import signature
from typing import Any, Callable, Dict


class Argument:
    def __init__(
        self,
        long_name: str,
        short_name: str,
        nargs: str,
        dest: str,
        type: Any,
        required: bool,
        flag: bool,
        help: str,
    ) -> None:
        self.short_name = short_name
        self.long_name = long_name
        self.nargs = nargs
        self.dest = dest
        self.type = type
        self.required = required
        self.flag = flag
        self.help = help


ARGUMENTS: Dict[str, Argument] = {}


def argument(
    long_name: str,
    short_name: str = None,
    nargs: str = None,
    required=False,
    flag=False,
    help: str = None,
) -> Callable:
    def wrapper(func: Callable):
        full_name = f"{func.__module__}.{func.__qualname__}"

        ARGUMENTS[full_name] = Argument(
            long_name,
            short_name,
            nargs,
            func.__name__,
            signature(func).return_annotation,
            required,
            flag,
            help,
        )

        return func

    return wrapper
