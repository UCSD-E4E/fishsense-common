from inspect import signature
from typing import Any, Callable, Dict, get_args


class Argument:
    def __init__(
        self,
        name: str,
        nargs: str,
        type: Any,
        required: bool,
        default: Any,
        help: str,
    ) -> None:
        self.name = name
        self.nargs = nargs
        self.type = type
        self.required = required
        self.default = default
        self.help = help


ARGUMENTS: Dict[str, Argument] = {}


def argument(
    name: str,
    nargs: str = None,
    required=False,
    default=None,
    help: str = None,
) -> Callable:
    def wrapper(func: Callable):
        full_name = f"{func.__module__}.{func.__qualname__}"
        argument_type = signature(func).return_annotation

        _nargs = nargs
        if argument_type.__name__ == "List":
            if _nargs is None:
                _nargs = "+" if required else "*"

            argument_type = get_args(argument_type)[0]

        ARGUMENTS[full_name] = Argument(
            name,
            _nargs,
            argument_type,
            required,
            default,
            help,
        )

        return func

    return wrapper
