"""
Base class for cli commands which allows for adding additional arguments to the cli.
"""

from abc import abstractmethod
from logging import Logger
from pathlib import Path

import ray
import yaml
from appdirs import user_config_dir

from fishsense_common import __version__
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

    @property
    def allow_config(self) -> bool:
        return True

    def __init__(self) -> None:
        self.__logger: Logger = None

    def save_config(self, save_config: str):
        class_name = f"{self.__class__.__module__}.{self.__class__.__qualname__}"
        args = {
            v.dest: getattr(self, v.dest)
            for k, v in ARGUMENTS.items()
            if k.startswith(class_name)
        }

        config = {self.name: {"args": args}}
        with open(save_config, "w") as f:
            yaml.safe_dump(config, f)

    def init_ray(self):
        ray_config_path = (
            Path(user_config_dir("RayCli", "Engineers for Exploration", __version__))
            / "ray.yaml"
        )

        ray_config = {}
        if ray_config_path.exists():
            with ray_config_path.open("r") as f:
                ray_config = yaml.safe_load(f)

        ray.init(**ray_config)

    @abstractmethod
    def __call__(self):
        """
        In a child class, this method is executed by a CLI plugin.
        """
        raise NotImplementedError
