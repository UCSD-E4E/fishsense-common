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

    def __call__(self):
        max_num_cpu = min(cpu_count(), self.__max_num_cpu or 0)
        max_num_gpu = min(
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
