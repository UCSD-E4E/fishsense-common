import math
from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable

import ray
import ray.remote_function
from tqdm import tqdm

from fishsense_common.scheduling.job import Job
from fishsense_common.scheduling.job_definition import JobDefinition


class RayJob(Job, ABC):
    @abstractmethod
    @property
    def job_count(self) -> int:
        raise NotImplementedError

    def __init__(
        self,
        job_definition: JobDefinition,
        function: Callable,
        num_cpus: float = None,
        num_gpus: float = None,
        vram_mb: int = None,
    ):
        super().__init__(job_definition)

        if num_gpus is None:
            import torch

            available_vram_mb = (
                float(torch.cuda.get_device_properties(0).total_memory) / 1024**2
            )
            percent_of_available_vram = float(vram_mb) / available_vram_mb

            # Ray only supports partial GPUs if we are requesting less than one.
            if percent_of_available_vram > 1:
                percent_of_available_vram = math.ceil(percent_of_available_vram)

            num_gpus = percent_of_available_vram

        if not hasattr(function, "remote"):
            function = ray.remote(function)

        self.__num_cpus: float = num_cpus
        self.__num_gpus: float = num_gpus
        self.__function: ray.remote_function.RemoteFunction = function

    def __to_iterator(self, futures: Iterable[ray.ObjectRef]) -> Iterable[Any]:
        while futures:
            done, futures = ray.wait(futures)
            yield ray.get(done[0])

    def __tqdm(self, futures: Iterable[ray.ObjectRef], **kwargs) -> Iterable[Any]:
        return tqdm(self.__to_iterator(futures), **kwargs)

    def __init_ray(self):
        ray.init(num_cpus=self.__num_cpus, num_gpus=self.__num_gpus)

    @abstractmethod
    def prologe(self) -> Iterable[Iterable[Any]]:
        raise NotImplementedError

    def run(self) -> None:
        self.__init_ray()

        parameters = self.prologe()

        results = self.__tqdm(
            (self.__function.remote(*p) for p in parameters),
            total=self.job_count,
            position=1,
            desc=self.job_definition.display_name,
        )

        self.epiloge(results)

    @abstractmethod
    def epiloge(self, results: Iterable[Any]) -> None:
        raise NotImplementedError
