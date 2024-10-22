import inspect
import logging
import os.path
import sys
from argparse import ArgumentParser
from typing import Dict

import yaml
from wakepy import keep

from fishsense_common.pluggable_cli.arguments import ARGUMENTS
from fishsense_common.pluggable_cli.command import Command


class Cli:
    def __init__(
        self,
        name: str = None,
        description: str = None,
        keep_awake=True,
    ):
        self._keep_awake = keep_awake
        self._logger = logging.getLogger(name)
        self._commands: Dict[str, Command] = {}
        self._name = name
        self._description = description

    def __parse(self) -> Command:
        config = {}
        if "--confg" in sys.argv:
            config_index = sys.argv.index("--config")
            value = sys.argv[config_index + 1]

            if os.path.exists(value):
                with open(value, "r") as f:
                    config = yaml.load(f)
            else:
                self._logger.warning(
                    f'"{value}" does not exist.  Skipping loading config.'
                )

        parser = ArgumentParser(prog=self._name, description=self._description)
        subparsers = parser.add_subparsers(dest="command")
        subparsers.required = True

        for name, command in self._commands.items():
            subparser = subparsers.add_parser(name, description=command.description)
            subparser.set_defaults(run_command=command)

            for member in inspect.getmembers(command):
                if member[0].startswith("_"):
                    continue

                full_name = f"{command.__class__.__module__}.{command.__class__.__qualname__}.{member[0]}"
                if full_name not in ARGUMENTS.keys():
                    continue

                argument = ARGUMENTS[full_name]

                args = [i for i in [argument.short_name, argument.long_name] if i]
                kwargs = {
                    "nargs": argument.nargs,
                    "dest": argument.dest,
                    "type": argument.type,
                    "required": argument.required,
                    "action": "store_true" if argument.flag else "store",
                    "default": argument.default,
                    "help": argument.help,
                }

                if (
                    name in config
                    and "args" in config[name]
                    and argument.dest in config[name]["args"]
                ):
                    kwargs["required"] = False
                    kwargs["default"] = config[name]["args"][argument.dest]

                if argument.nargs:
                    del kwargs["dest"]
                    del kwargs["required"]

                if argument.flag:
                    del kwargs["nargs"]
                    del kwargs["type"]

                subparser.add_argument(*args, **kwargs)

            subparser.add_argument(
                "--config",
                dest="config",
                type=str,
                required=False,
                default=None,
                help="A yaml configuration file which can be overrode by the command line arguments.",
            )

        args = parser.parse_args()
        command: Command = args.run_command

        for member in inspect.getmembers(command):
            if member[0].startswith("_"):
                continue

            full_name = f"{command.__class__.__module__}.{command.__class__.__qualname__}.{member[0]}"
            if full_name not in ARGUMENTS.keys():
                continue

            argument = ARGUMENTS[full_name]

            setattr(command, member[0], getattr(args, argument.dest))

        return command

    def add(self, command: Command) -> None:
        self._commands[command.name] = command

    def __call__(self):
        command = self.__parse()

        sleep_hold_set = False
        if self._keep_awake:
            try:
                sleep_hold = keep.running()
                sleep_hold.__enter__()
                sleep_hold_set = True
            except:
                self._logger.warning(
                    "Exception occurred while trying to get a sleep hold.  Computer may sleep."
                )

        command()

        if sleep_hold_set:
            sleep_hold.__exit__(None, None, None)
