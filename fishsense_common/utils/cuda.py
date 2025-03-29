import os
from typing import List


def get_most_free_gpu() -> int | None:
    import cupy

    if cupy.cuda.is_available():
        free_memory: List[int] = []

        for i in range(cupy.cuda.runtime.getDeviceCount()):
            with cupy.cuda.Device(i):
                # Index 0 is free memory, index 1 is total memory
                free_memory.append(cupy.cuda.runtime.memGetInfo()[0])

        most_free_gpu = free_memory.index(max(free_memory))
        return most_free_gpu
    else:
        return None


def get_pytorch_device() -> str:
    import torch

    if torch.cuda.is_available():
        return f"cuda:{get_most_free_gpu()}"
    else:
        return "cpu"


def set_opencv_opencl_device() -> None:
    os.environ["OPENCV_OPENCL_DEVICE"] = f":GPU:{get_most_free_gpu()}"
