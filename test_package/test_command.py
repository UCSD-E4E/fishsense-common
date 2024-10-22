from typing import List

from fishsense_common.pluggable_cli.arguments import argument
from fishsense_common.pluggable_cli.command import Command


class TestCommand(Command):
    @property
    def name(self) -> str:
        return "test-command"

    @property
    def description(self) -> str:
        return "Test command description."

    @property
    @argument(
        "--test-argument", short_name="-t", required=True, help="Test help description."
    )
    def test_argument(self) -> List[str]:
        return self._test_argument

    @test_argument.setter
    def test_argument(self, value: List[str]):
        self._test_argument = value

    def __init__(self) -> None:
        super().__init__()

        self._test_argument: str = None

    def __call__(self):
        print(self.test_argument)
