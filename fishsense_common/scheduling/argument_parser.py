import math
from abc import ABC, abstractmethod
from typing import Any, List, Set

from fishsense_common.scheduling.arguments import Argument


class ArgumentParser(ABC):
    @property
    @abstractmethod
    def priority(self) -> float:
        raise NotImplementedError

    @abstractmethod
    def can_parse(self, argument: Argument) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, argument: Argument, value: Any):
        raise NotImplementedError


class __ListArgumentParser(ArgumentParser):
    @property
    def priority(self) -> float:
        return 1

    def can_parse(self, argument: Argument) -> bool:
        return argument.nargs == "+" or argument.nargs == "*"

    def parse(self, argument: Argument, value: List[Any]):
        if all(isinstance(v, argument.type) for v in value):
            return value

        return [argument.type(v) for v in value]


class __GenericArgumentParser(ArgumentParser):
    @property
    def priority(self) -> float:
        return math.inf

    def can_parse(self, _: Argument) -> bool:
        return True

    def parse(self, argument: Argument, value: str):
        return argument.type(value)


__ARGUMENT_PARSERS: Set[ArgumentParser] = set()


def add_argument_parser(parser: ArgumentParser):
    __ARGUMENT_PARSERS.add(parser)


def parse_argument(argument: Argument, value: str) -> Any:
    type_parser = next(
        t
        for t in sorted(__ARGUMENT_PARSERS, key=lambda p: p.priority)
        if t.can_parse(argument)
    )
    return type_parser.parse(argument, value)


add_argument_parser(__ListArgumentParser())
add_argument_parser(__GenericArgumentParser())
