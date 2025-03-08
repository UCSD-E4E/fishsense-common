import importlib
from argparse import ArgumentParser
from pathlib import Path
from typing import List

import yaml
from tqdm import tqdm

from fishsense_common.scheduling.job import Job
from fishsense_common.scheduling.job_definition import JobYaml


class CliScheduler:
    def run(self, name: str, description: str):
        parser = ArgumentParser(name, description)

        parser.add_argument(
            "job_definition_globs",
            nargs="+",
            help="The job definition to run.",
        )

        args = parser.parse_args()
        job_definitions_path: List[Path] = [
            p for g in args.job_definition_globs for p in Path(g).glob()
        ]

        for path in tqdm(job_definitions_path, position=0, desc="Running jobs"):
            with open(path, "r") as f:
                job_yaml: JobYaml = yaml.safe_load(f)

            for job_definition in job_yaml.jobs:
                module = importlib.import_module(job_definition.module)
                class_type = getattr(module, job_definition.class_name)

                class_instance: Job = class_type(job_definition)
                class_instance.run()
