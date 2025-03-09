from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path
from typing import Any, List

import yaml
from tqdm import tqdm

from fishsense_common.scheduling.job import Job
from fishsense_common.scheduling.job_definition import JobYaml
from fishsense_common.scheduling.scheduler import Scheduler


class CliScheduler(Scheduler):
    def __init__(self, name: str = None, description: str = None):
        super().__init__()

        self.__parser = ArgumentParser(prog=name, description=description)
        subparsers = self.__parser.add_subparsers(dest="command")
        subparsers.required = True

        self.__register_list_jobs_command(subparsers)
        self.__register_run_jobs_command(subparsers)

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

    def __run_jobs_command(self, args: Any):
        job_definitions_path: List[Path] = [
            p for g in args.job_definition_globs for p in Path(".").glob(g)
        ]

        for path in tqdm(job_definitions_path, position=0, desc="Running jobs"):
            with open(path, "r") as f:
                job_yaml: JobYaml = yaml.safe_load(f)

            for job_definition in job_yaml.jobs:
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

    def __call__(self):
        args = self.__parser.parse_args()
        args.run_command(args)
