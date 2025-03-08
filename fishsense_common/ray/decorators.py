import math

import ray


def remote(vram_mb: int):
    import torch

    if not torch.cuda.is_available():
        return ray.remote

    available_vram_mb = (
        float(torch.cuda.get_device_properties(0).total_memory) / 1024**2
    )
    percent_of_available_vram = float(vram_mb) / available_vram_mb

    if percent_of_available_vram > 1:
        percent_of_available_vram = math.ceil(percent_of_available_vram)

    return ray.remote(num_gpus=percent_of_available_vram)
