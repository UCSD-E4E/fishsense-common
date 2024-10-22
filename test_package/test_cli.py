from fishsense_common.pluggable_cli.ray_cli import RayCli
from test_package.test_command import TestCommand

if __name__ == "__main__":
    cli = RayCli(name="test-package", description="Test package description.")

    cli.add(TestCommand())

    cli()
