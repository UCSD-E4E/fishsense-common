from abc import ABC

from fishsense_common import __version__
from fishsense_common.pluggable_cli.cli import Cli
from fishsense_common.pluggable_cli.generate_ray_config_command import (
    GenerateRayConfigCommand,
)


class RayCli(Cli, ABC):
    def __init__(self, name: str = None, description: str = None, keep_awake=True):
        super().__init__(name, description, keep_awake)

        self.add(GenerateRayConfigCommand())

    def __call__(self):
        return super().__call__()
