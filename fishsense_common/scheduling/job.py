from abc import ABC, abstractmethod
from typing import Any

from fishsense_common.scheduling.argument_parser import parse_argument
from fishsense_common.scheduling.arguments import ARGUMENTS, Argument
from fishsense_common.scheduling.job_definition import JobDefinition


class Job(ABC):
    @property
    def job_definition(self) -> JobDefinition:
        return self.__job_definition

    def __init__(
        self,
        job_definition: JobDefinition,
        input_filesystem: Any,
        output_filesystem: Any,
    ):
        super().__init__()

        if not hasattr(self, "name"):
            raise ValueError("Job must have a name. Please define a name attribute.")

        self.__job_definition = job_definition
        self.input_filesystem = input_filesystem
        self.output_filesystem = output_filesystem
        self.__fill_parameters()

    def __get_argument(self, class_object: type, member: str) -> Argument:
        full_name = f"{class_object.__module__}.{class_object.__qualname__}.{member}"
        if full_name in ARGUMENTS.keys():
            return ARGUMENTS[full_name]

        bases = [b for b in class_object.__mro__ if b != class_object]
        # If we only have object as a super.
        if len(bases) <= 1:
            return None

        # Recursively look at the supers for arguments.
        arguments = [self.__get_argument(b, member) for b in bases]
        arguments = [a for a in arguments if a is not None]

        # If we have at least 1, let's grab the first one.
        if len(arguments) > 0:
            return arguments[0]

        # If we don't have any, return
        return None

    def __fill_parameters(self):
        for member in dir(self):
            if member.startswith("_"):
                continue

            argument = self.__get_argument(self.__class__, member)
            if argument is None:
                continue

            if argument.name not in self.job_definition.parameters:
                if argument.required:
                    raise ValueError(
                        f"Argument {argument.name} is required but not provided."
                    )

                setattr(
                    self,
                    member,
                    argument.default,
                )
                continue

            if argument.nargs == "+" and not isinstance(
                self.job_definition.parameters[argument.name], list
            ):
                raise ValueError(
                    f"Argument {argument.name} is a list but not provided as a list."
                )

            if argument.nargs == "*" and not isinstance(
                self.job_definition.parameters[argument.name], list
            ):
                self.job_definition.parameters[argument.name] = [
                    self.job_definition.parameters[argument.name]
                ]

            setattr(
                self,
                member,
                parse_argument(argument, self.job_definition.parameters[argument.name]),
            )

    @abstractmethod
    def __call__(self) -> None:
        raise NotImplementedError
