import os


def get_most_free_gpu() -> int | None:
    import cupy

    if cupy.cuda.is_available():
        # Index 0 is free memory, index 1 is total memory
        free_memory = [
            cupy.cuda.runtime.memGetInfo(i)[0]
            for i in range(cupy.cuda.runtime.getDeviceCount())
        ]
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
