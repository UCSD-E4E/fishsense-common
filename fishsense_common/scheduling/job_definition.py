from typing import Any, Dict


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
