import inspect
from typing import Callable, List, Tuple


class Pipeline:
    def __init__(self, *tasks: List[Callable]):
        self.__tasks = tasks

    def __call__(self, **kwargs):
        for task in self.__tasks:
            output_name: str | Tuple[str, ...] = getattr(task, "output_name", None)

            task_signature = inspect.signature(task)
            task_parameters = task_signature.parameters
            results = task(*(kwargs[param] for param in task_parameters))

            if output_name:
                if isinstance(output_name, str):
                    kwargs[output_name] = results
                else:
                    for name, result in zip(output_name, results):
                        kwargs[name] = result
