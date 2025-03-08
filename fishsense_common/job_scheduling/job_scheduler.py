import importlib
from abc import ABC
from inspect import signature
from pathlib import Path
from threading import Lock, Thread
from time import sleep
from typing import Any, Callable, Dict, Generator, Iterable, List

import ray
import yaml
from tqdm import tqdm

from fishsense_common.job_scheduling.decorators.job import JobMetadata


class JobDefinition(yaml.YAMLObject):
    yaml_tag = "!JobDefinition"

    def __init__(
        self, package: str, module: str, function: str, parameters: Dict[str, Any]
    ):
        self.package = package
        self.module = module
        self.function = function
        self.parameters = parameters


class JobScheduler(ABC):
    def __init__(self):
        super().__init__()

        self.__lock = Lock()
        self.__scheduled_jobs: List[JobDefinition] = []
        self.__thread = Thread(target=self.__run_jobs)
        self.__thread.start()

    def __push_job(self, job_definition: JobDefinition):
        with self.__lock:
            self.__scheduled_jobs.append(job_definition)

    def __pop_job(self, job_definition: JobDefinition):
        with self.__lock:
            return self.__scheduled_jobs.pop(job_definition)

    def __any_jobs(self) -> bool:
        with self.__lock:
            return len(self.__scheduled_jobs) > 0

    def __run_jobs(self):
        while True:
            while self.__any_jobs():
                job_definition = self.__pop_job()
                self.__run_job(job_definition)

            sleep(10)  # Wait 10 seconds before checking for new jobs.

    def __run_job(self, job_definition: JobDefinition):
        module = importlib.import_module(
            f".{job_definition['module']}", job_definition["package"]
        )

        if not module:
            raise ImportError(
                f"Could not import module {job_definition['module']} from package {job_definition['package']}."
            )

        if not hasattr(module, job_definition.function):
            raise AttributeError(
                f"Module {job_definition['module']} does not have a function {job_definition['function']}."
            )

        function = getattr(module, job_definition.function)

        if not hasattr(function, "job_metadata"):
            raise AttributeError(
                f"Function {job_definition['function']} does not have job metadata."
            )

        job_metadata: JobMetadata = function.job_metadata
        parameters = list(
            self.__parse_parameters(job_definition, job_metadata, function)
        )  # Need to convert this to list to be able iterate over it many times

        counts = [len(p) if isinstance(list) else 1 for p in parameters]
        total_counts = {c for c in counts if c != 1}

        if len(total_counts) > 1:
            raise ValueError(
                "All parameters must have the same number of values or be single values."
            )

        parameters = self.__expand_parameters(parameters, total_counts.pop())

        if job_metadata.parallel:
            function = ray.remote(function)(
                job_metadata.num_cpus, job_metadata.num_gpus
            )

            futures = [function.remote(*p) for p in parameters]
        else:
            for p in tqdm(parameters):
                function(*p)

    def __parse_parameters(
        self,
        job_definition: JobDefinition,
        job_metadata: JobMetadata,
        function: Callable,
    ) -> Generator[Any]:
        signature_parameters = signature(function).parameters
        ordered_parameter_keys = list(job_definition.parameters.keys())

        if any(
            parameter_key not in signature_parameters
            for parameter_key in ordered_parameter_keys
        ):
            raise KeyError(
                "Some parameters are not defined in the function signature. Please ensure @parameter decorator to and function signature match."
            )

        ordered_parameter_keys.sort(key=lambda x: signature_parameters[x].position)

        for parameter_key in ordered_parameter_keys:
            parameter_type = signature_parameters[parameter_key].annotation
            parameter_value = job_definition.parameters.get(parameter_key)

            if parameter_key not in job_metadata.parameters:
                raise KeyError(
                    f"Parameter {parameter_key} not found in job metadata. Please use the @parameter decorator to define it."
                )

            parameter_definition = job_metadata.parameters.get(parameter_key)

            if parameter_definition.allow_many:
                value = []
                for parameter in parameter_value:
                    if parameter_type is Path and parameter_definition.allow_glob:
                        value.extend(Path.glob(parameter))
                    else:
                        value.append(parameter_type(parameter, parameter_definition))
            else:
                if parameter_type is Path and parameter_definition.allow_glob:
                    value = Path.glob(parameter_value)
                else:
                    value = parameter_type(parameter_value)

            yield value

    def __expand_parameters(
        self, parameters: List[List[Any]], count: int
    ) -> Generator[List[Any]]:
        for i in range(count):
            yield [p if not isinstance(p, list) else p[i] for p in parameters]

    def schedule(self, job_definition: JobDefinition):
        self.__push_job(job_definition)

    def tqdm(self, futures: Iterable[ray.ObjectRef], **kwargs) -> Iterable[Any]:
        return tqdm(self.__to_iterator(futures), **kwargs)
