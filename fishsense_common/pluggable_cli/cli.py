import inspect
import logging
import os.path
import sys
from argparse import ArgumentParser, _SubParsersAction
from typing import Dict, Tuple

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
        self.__keep_awake = keep_awake
        self.__logger = logging.getLogger(name)
        self.__commands: Dict[str, Command] = {}
        self.__name = name
        self.__description = description

    def __parse(self) -> Command:
        config = {}
        if "--config" in sys.argv:
            config_index = sys.argv.index("--config")
            value = sys.argv[config_index + 1]

            if os.path.exists(value):
                with open(value, "r") as f:
                    config = yaml.safe_load(f)
            else:
                self.__logger.warning(
                    f'"{value}" does not exist.  Skipping loading config.'
                )

        parser = ArgumentParser(prog=self.__name, description=self.__description)
        subparsers = parser.add_subparsers(dest="command")
        subparsers.required = True

        for name, command in self.__commands.items():
            command.logger = self.__logger

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
                    command.allow_config
                    and name in config
                    and "args" in config[name]
                    and argument.dest in config[name]["args"]
                ):
                    kwargs["required"] = False
                    kwargs["default"] = config[name]["args"][argument.dest]

                    if kwargs["nargs"] == "+":
                        kwargs["nargs"] = "*"

                if argument.nargs:
                    del kwargs["dest"]
                    del kwargs["required"]

                if argument.flag:
                    del kwargs["nargs"]
                    del kwargs["type"]

                subparser.add_argument(*args, **kwargs)

            if command.allow_config:
                subparser.add_argument(
                    "--config",
                    dest="config",
                    type=str,
                    required=False,
                    default=None,
                    help="A yaml configuration file which can be overrode by the command line arguments.",
                )

                subparser.add_argument(
                    "--save-config",
                    dest="save_config",
                    type=str,
                    required=False,
                    default=None,
                    help="A path to save a yaml file with the current configuration of the command line arguments.",
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

        if hasattr(args, "save_config") and args.save_config:
            command.save_config(args.save_config)

            return None
        else:
            return command

    def add(self, command: Command) -> None:
        self.__commands[command.name] = command

    def __call__(self):
        command = self.__parse()

        sleep_hold_set = False
        if self.__keep_awake:
            try:
                sleep_hold = keep.running()
                sleep_hold.__enter__()
                sleep_hold_set = True
            except:
                self.__logger.warning(
                    "Exception occurred while trying to get a sleep hold.  Computer may sleep."
                )

        if command:
            command()

        if sleep_hold_set:
            sleep_hold.__exit__(None, None, None)
