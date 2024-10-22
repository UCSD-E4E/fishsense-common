"""
Base class for cli commands which allows for adding additional arguments to the cli.
"""

from abc import abstractmethod
from logging import Logger

import yaml

from fishsense_common.pluggable_cli.arguments import ARGUMENTS


class Command:
    """
    Base class for cli commands which allows for adding additional arguments to the cli.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        raise NotImplementedError

    @property
    def logger(self) -> Logger:
        return self.__logger

    @logger.setter
    def logger(self, value: Logger):
        self.__logger = value

    def __init__(self) -> None:
        self.__logger: Logger = None

    def __save_config(self, save_config: str):
        class_name = f"{self.__class__.__module__}.{self.__class__.__qualname__}"
        args = {k: v for k, v in ARGUMENTS.items() if k.startswith(class_name)}

        config = {"command": self.name, "args": args}
        with open(save_config, "w") as f:
            yaml.dump(config, f)

    @abstractmethod
    def __call__(self):
        """
        In a child class, this method is executed by a CLI plugin.
        """
        raise NotImplementedError
