import math
from typing import Callable, Dict

from fishsense_common.job_scheduling.decorators.parameter import Parameter


class JobMetadata:
    def __init__(
        self,
        name: str,
        parallel: bool,
        num_cpus: int,
        num_gpus: float,
    ):
        self.name = name
        self.parallel = parallel
        self.num_cpus = num_cpus
        self.num_gpus = num_gpus
        self.parameters: Dict[str, Parameter] = {}


def job(
    name: str,
    parallel: bool = False,
    num_cpus: int = None,
    num_gpus: float = None,
    vram_mb: int = None,
):

    def wrapper(function: Callable):
        final_num_gpus = num_gpus
        if vram_mb and not final_num_gpus:
            import torch

            if torch.cuda.is_available():
                available_vram_mb = (
                    float(torch.cuda.get_device_properties(0).total_memory) / 1024**2
                )
                percent_of_available_vram = float(vram_mb) / available_vram_mb

                # Ray only supports partial GPUs if we are requesting less than one.
                if percent_of_available_vram > 1:
                    percent_of_available_vram = math.ceil(percent_of_available_vram)

                final_num_gpus = percent_of_available_vram

        metadata = JobMetadata(name, parallel, num_cpus, final_num_gpus)

        setattr(function, "job_metadata", metadata)
        return function

    return wrapper
