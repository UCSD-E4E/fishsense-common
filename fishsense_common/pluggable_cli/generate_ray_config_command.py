from multiprocessing import cpu_count
from pathlib import Path

import torch
import yaml
from appdirs import user_config_dir

from fishsense_common import __version__
from fishsense_common.pluggable_cli.arguments import argument
from fishsense_common.pluggable_cli.command import Command


class GenerateRayConfigCommand(Command):
    @property
    def allow_config(self) -> bool:
        return False

    @property
    def name(self):
        return "generate-ray-config"

    @property
    def description(self):
        return "Generates a Ray config that can be used to customize the consumption of Ray commands."

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

    def __init__(self):
        self.__max_num_cpu: int = None
        self.__max_num_gpu: int = None

    def __call__(self):
        max_num_cpu = max(cpu_count(), self.__max_num_cpu or 0)
        max_num_gpu = max(
            torch.cuda.device_count() if torch.cuda.is_available() else 1000,
            self.__max_num_gpu or 0,
        )

        if max_num_gpu == 0 or max_num_gpu == 1000:
            max_num_gpu = None

        self.logger.debug(f"num_cpus: {max_num_cpu}")
        self.logger.debug(f"num_gpus: {max_num_gpu}")

        config = {"num_cpus": max_num_cpu}

        if max_num_gpu:
            config["num_gpus"] = max_num_gpu

        config_path = (
            Path(user_config_dir("RayCli", "Engineers for Exploration", __version__))
            / "ray.yaml"
        )
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with config_path.open("w") as f:
            yaml.safe_dump(config, f)
