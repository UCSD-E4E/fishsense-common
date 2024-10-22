"""
Base class for cli commands which allows for adding additional arguments to the cli.
"""

from abc import abstractmethod
from argparse import ArgumentParser, Namespace
from logging import Logger


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

    # def __init__(self, parser: ArgumentParser, logger: Logger):
    #     self.logger = logger

    @abstractmethod
    def __call__(self, args: Namespace):
        """
        In a child class, this method is executed by a CLI plugin.
        """
        raise NotImplementedError
