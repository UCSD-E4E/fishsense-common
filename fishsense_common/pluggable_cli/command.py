"""
Base class for cli commands which allows for adding additional arguments to the cli.
"""

from abc import abstractmethod
from logging import Logger
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any, Iterable, Tuple

import ray
import torch
import yaml
from appdirs import user_config_dir
from tqdm import tqdm

from fishsense_common import __version__
from fishsense_common.pluggable_cli.arguments import ARGUMENTS, argument


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

    @property
    @argument("--max-cpu", help="Sets the maximum number of CPU cores allowed.")
    def max_num_cpu(self) -> int:
        return self.__max_num_cpu

    @max_num_cpu.setter
    def max_num_cpu(self, value: int):
        self.__max_num_cpu = value

    @property
    @argument("--max-gpu", help="Sets the maximum number of GPU kernels allowed.")
    def max_num_gpu(self) -> int:
        return self.__max_num_gpu

    @max_num_gpu.setter
    def max_num_gpu(self, value: int):
        self.__max_num_gpu = value

    def __init__(self) -> None:
        self.__logger: Logger = None
        self.__max_num_cpu: int = None
        self.__max_num_gpu: int = None

    def __to_iterator(self, futures: Iterable[ray.ObjectRef]) -> Iterable[Any]:
        while futures:
            done, futures = ray.wait(futures)
            yield ray.get(done[0])

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

    def init_ray(self) -> Tuple[int, int]:
        ray_config_path = (
            Path(user_config_dir("RayCli", "Engineers for Exploration", __version__))
            / "ray.yaml"
        )

        ray_config = {}
        if ray_config_path.exists():
            with ray_config_path.open("r") as f:
                ray_config = yaml.safe_load(f)

        # Allow override of num_cpus and num_gpus.
        if self.max_num_cpu is not None:
            ray_config["num_cpus"] = min(cpu_count(), self.__max_num_cpu or 0)

        if self.max_num_gpu is not None:
            ray_config["num_gpus"] = min(
                torch.cuda.device_count() if torch.cuda.is_available() else 1000,
                self.__max_num_gpu or 0,
            )

        ray.init(**ray_config)

        return ray_config["num_cpus"], (
            ray_config["num_gpus"] if "num_gpus" in ray_config else None
        )

    def tqdm(self, futures: Iterable[ray.ObjectRef], **kwargs) -> Iterable[Any]:
        return tqdm(self.__to_iterator(futures), **kwargs)

    @abstractmethod
    def __call__(self):
        """
        In a child class, this method is executed by a CLI plugin.
        """
        raise NotImplementedError
