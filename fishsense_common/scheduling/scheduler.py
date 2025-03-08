from abc import ABC, abstractmethod
from typing import Callable, Dict


class Scheduler(ABC):
    def __init__(self):
        super().__init__()

        self.job_types: Dict[str, Callable] = {}

    def register_job_type(self, job_type: Callable):
        if not hasattr(job_type, "name"):
            raise ValueError(f"Job type {job_type} does not have a name.")

        job_type_name: str = getattr(job_type, "name")

        if job_type_name in self.job_types:
            raise ValueError(f"Job type {job_type_name} already exists.")

        self.job_types[job_type_name] = job_type

    @abstractmethod
    def __call__(self):
        raise NotImplementedError
