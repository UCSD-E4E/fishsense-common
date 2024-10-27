from fishsense_common.pluggable_cli.cli import Cli
from test_package.test_command import TestCommand

if __name__ == "__main__":
    cli = Cli(name="test-package", description="Test package description.")

    cli.add(TestCommand())

    cli()
