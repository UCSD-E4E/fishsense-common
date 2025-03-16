import inspect
import math
import sys
from abc import ABC, abstractmethod
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any, Callable, Iterable, List, Tuple

import ray
import ray.remote_function
import yaml
from platformdirs import user_config_dir
from tqdm import tqdm

from fishsense_common import __version__
from fishsense_common.scheduling.arguments import argument
from fishsense_common.scheduling.job import Job
from fishsense_common.scheduling.job_definition import JobDefinition


class RayJob(Job, ABC):
    @property
    @abstractmethod
    def job_count(self) -> int:
        raise NotImplementedError

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

    @property
    def __debugger_attached(self) -> bool:
        for frame in inspect.stack():
            if "pydevd" in frame.filename:
                return True

        return sys.gettrace() is not None

    def __init__(
        self,
        job_definition: JobDefinition,
        function: Callable,
        vram_mb: int = None,
    ):
        super().__init__(job_definition)

        num_gpus = None
        if vram_mb is not None:
            import torch

            available_vram_mb = (
                float(torch.cuda.get_device_properties(0).total_memory) / 1024**2
            )
            percent_of_available_vram = float(vram_mb) / available_vram_mb

            # Ray only supports partial GPUs if we are requesting less than one.
            if percent_of_available_vram > 1:
                percent_of_available_vram = math.ceil(percent_of_available_vram)

            num_gpus = percent_of_available_vram

        if not hasattr(function, "remote") and not self.__debugger_attached:
            function = ray.remote(num_gpus=num_gpus)(function)

        self.__max_num_cpu: int = None
        self.__max_num_gpu: int = None
        self.__function: ray.remote_function.RemoteFunction = function

    def __to_iterator(self, futures: Iterable[ray.ObjectRef]) -> Iterable[Any]:
        while futures:
            done, futures = ray.wait(futures)
            yield ray.get(done[0])

    def __tqdm(self, futures: Iterable[ray.ObjectRef], **kwargs) -> Iterable[Any]:
        return tqdm(self.__to_iterator(futures), **kwargs)

    def __init_ray(self) -> Tuple[float, float]:
        import torch

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

    @abstractmethod
    def prologue(self) -> Iterable[Iterable[Any]]:
        raise NotImplementedError

    def __call__(self) -> None:
        self.__init_ray()

        parameters = self.prologue()

        if hasattr(self.__function, "remote"):
            results = self.__tqdm(
                [self.__function.remote(*p) for p in parameters],
                total=self.job_count,
                position=2,
                desc=self.job_definition.display_name,
            )
        else:
            results = tqdm(
                (self.__function(*p) for p in parameters),
                total=self.job_count,
                position=2,
                desc=self.job_definition.display_name,
            )

        self.epiloge(results)

        ray.shutdown()

    @abstractmethod
    def epiloge(self, results: List[ray.ObjectRef]) -> None:
        raise NotImplementedError
