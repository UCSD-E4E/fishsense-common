import inspect
from typing import Any, Callable, Dict, List, Tuple

from fishsense_common.pipeline.status import Status


class Pipeline:
    def __init__(self, *tasks: List[Callable], return_name: str | Tuple[str] = None):
        self.__tasks = tasks
        self.__return_name = return_name

    def __call__(self, **kwargs) -> Tuple[Dict[str, bool], Any]:
        statuses: Dict[str, bool] = {}

        for task in self.__tasks:
            output_name: str | Tuple[str, ...] = getattr(task, "output_name", None)

            task_signature = inspect.signature(task)
            task_parameters = task_signature.parameters
            status = task(*(kwargs[param] for param in task_parameters))

            if isinstance(status, Status):
                statuses[task.__name__] = status.status

                if not status:
                    if self.__return_name is not None:
                        if isinstance(self.__return_name, str):
                            return statuses, None
                        else:
                            return statuses, tuple(None for name in self.__return_name)

                results = status.return_value
            else:
                results = status

            if output_name:
                if isinstance(output_name, str):
                    kwargs[output_name] = results
                else:
                    for name, result in zip(output_name, results):
                        kwargs[name] = result

        if self.__return_name is not None:
            if isinstance(self.__return_name, str):
                return statuses, kwargs[self.__return_name]
            else:
                return statuses, tuple(kwargs[name] for name in self.__return_name)
