from argparse import ArgumentParser, _SubParsersAction
from glob import glob
from multiprocessing import cpu_count
from pathlib import Path
from typing import Any, List

import yaml
from platformdirs import user_config_dir
from tqdm import tqdm

from fishsense_common import __version__
from fishsense_common.scheduling.job import Job
from fishsense_common.scheduling.job_definition import JobDefinition
from fishsense_common.scheduling.scheduler import Scheduler


class CliScheduler(Scheduler):
    def __init__(self, name: str = None, description: str = None):
        super().__init__()

        self.__parser = ArgumentParser(prog=name, description=description)
        subparsers = self.__parser.add_subparsers(dest="command")
        subparsers.required = True

        self.__register_list_jobs_command(subparsers)
        self.__register_run_jobs_command(subparsers)
        self.__register_generate_ray_config(subparsers)

    def __register_list_jobs_command(self, subparsers: _SubParsersAction):
        subparser: ArgumentParser = subparsers.add_parser(
            "list-jobs", description="Lists all available jobs."
        )
        subparser.set_defaults(run_command=self.__list_jobs_command)

    def __register_run_jobs_command(self, subparsers: _SubParsersAction):
        subparser: ArgumentParser = subparsers.add_parser(
            "run-jobs", description="Runs a job file."
        )
        subparser.set_defaults(run_command=self.__run_jobs_command)

        subparser.add_argument(
            "job_definition_globs",
            nargs="+",
            help="The job definition to run.",
        )

    def __register_generate_ray_config(self, subparsers: _SubParsersAction):
        subparser: ArgumentParser = subparsers.add_parser(
            "generate-ray-config",
            description="Generates a Ray config that can be used to customize the consumption of Ray commands.",
        )
        subparser.set_defaults(run_command=self.__generate_ray_config_command)

        subparser.add_argument(
            "--max-cpu",
            "-c",
            dest="max_num_cpu",
            default=1000,
            type=int,
            help="Sets the maximum number of CPU cores allowed.",
        )

        subparser.add_argument(
            "--max-gpu",
            "-g",
            dest="max_num_gpu",
            default=1000,
            type=int,
            help="Sets the maximum number of GPU kernels allowed.",
        )

    def __run_jobs_command(self, args: Any):
        job_definitions_path: List[Path] = [
            Path(f) for g in args.job_definition_globs for f in glob(g)
        ]

        for path in tqdm(job_definitions_path, position=0, desc="Running jobs"):
            with open(path, "r") as f:
                job_dict = yaml.safe_load(f)

            if "jobs" not in job_dict:
                raise ValueError("No jobs found in job definition.")

            jobs = (JobDefinition(**j) for j in job_dict["jobs"])

            for job_definition in jobs:
                if job_definition.job_name not in self.job_types:
                    raise ValueError(f"Job type {job_definition.job_name} not found.")

                job_type = self.job_types[job_definition.job_name]
                job = job_type(job_definition)

                if not isinstance(job, Job):
                    raise ValueError(f"Job {job_definition.job_name} is not a Job.")

                job()

    def __list_jobs_command(self, args: Any):
        print("Registered Job Types:")
        for job_type in self.job_types.keys():
            print(f"  - {job_type}")

    def __generate_ray_config_command(self, args: Any):
        import torch  # We want to avoid importing

        max_num_cpu = min(cpu_count(), args.max_num_cpu)
        max_num_gpu = min(
            torch.cuda.device_count() if torch.cuda.is_available() else 1000,
            args.max_num_gpu or 0,
        )

        if max_num_gpu == 0 or max_num_gpu == 1000:
            max_num_gpu = None

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

    def __call__(self):
        args = self.__parser.parse_args()
        args.run_command(args)
