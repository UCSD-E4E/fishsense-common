from typing import Any, Dict, List

import yaml


class JobDefinition:
    def __init__(
        self,
        display_name: str,
        job_name: str,
        parameters: Dict[str, Any],
    ):
        self.display_name = display_name
        self.job_name = job_name
        self.parameters = parameters


class JobYaml(yaml.YAMLObject):
    yaml_tag = "!JobDefinition"

    def __init__(self, jobs: List[JobDefinition]):
        super().__init__()

        self.jobs = jobs
