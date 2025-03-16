from typing import Callable, Tuple


def task(output_name: str | Tuple[str, ...] = None):
    def wrapper(func: Callable):
        func.output_name = output_name

        return func

    return wrapper
