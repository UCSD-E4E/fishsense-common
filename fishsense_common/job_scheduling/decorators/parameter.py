from typing import Callable


class Parameter:
    def __init__(self, name: str, required: bool, allow_many: bool, allow_glob: bool):
        self.name = name
        self.required = required
        self.allow_many = allow_many
        self.allow_glob = allow_glob


def parameter(
    name: str,
    type: type,
    required: bool = False,
    allow_many: bool = False,
    allow_glob: bool = False,
):
    from fishsense_common.job_scheduling.decorators.job import (
        JobMetadata,  # Prevent circular import
    )

    def wrapper(function: Callable):
        if not hasattr(function, "job_metadata"):
            raise Exception(
                f"{function.__name__} is not a job function. Please use the @job decorator."
            )

        job_metadata: JobMetadata = getattr(function, "job_metadata")

        job_metadata.parameters[name] = Parameter(
            name, type, required, allow_many, allow_glob
        )

    return wrapper
