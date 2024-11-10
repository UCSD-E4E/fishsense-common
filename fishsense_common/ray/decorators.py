import math

import ray
import torch


def remote(vram_mb: int):
    available_vram_mb = (
        float(torch.cuda.get_device_properties(0).total_memory) / 1024**2
    )
    percent_of_available_vram = float(vram_mb) / available_vram_mb

    if percent_of_available_vram > 1:
        percent_of_available_vram = math.ceil(percent_of_available_vram)

    return ray.execute(num_gpus=percent_of_available_vram)
