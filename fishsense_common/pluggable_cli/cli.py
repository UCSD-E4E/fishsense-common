import inspect
import logging
import os.path
import sys
from argparse import ArgumentParser
from typing import Dict

import yaml
from wakepy import keep

from fishsense_common.pluggable_cli.arguments import ARGUMENTS, Argument
from fishsense_common.pluggable_cli.command import Command
from fishsense_common.pluggable_cli.generate_ray_config_command import (
    GenerateRayConfigCommand,
)


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

        self.add(GenerateRayConfigCommand())

    def __get_argument(self, class_object: type, member: str) -> Argument:
        full_name = f"{class_object.__module__}.{class_object.__qualname__}.{member}"
        if full_name in ARGUMENTS.keys():
            return ARGUMENTS[full_name]

        bases = [b for b in class_object.__mro__ if b != class_object]
        # If we only have object as a super.
        if len(bases) <= 1:
            return None

        # Recursively look at the supers for arguments.
        arguments = [self.__get_argument(b, member) for b in bases]
        arguments = [a for a in arguments if a is not None]

        # If we have at least 1, let's grab the first one.
        if len(arguments) > 0:
            return arguments[0]

        # If we don't have any, return
        return None

    def __parse(self) -> Command:
        value = None
        if "--config" in sys.argv:
            config_index = sys.argv.index("--config")
            value = sys.argv[config_index + 1]
        elif any(True for v in sys.argv if v.startswith("--config=")):
            value = [v.replace("--config=") for v in sys.argv.startswith("--config=")][
                0
            ]

        config = {}
        if value is not None:
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

                argument = self.__get_argument(command.__class__, member[0])
                if argument is None:
                    continue

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
                    and config[name]["args"][argument.dest] is not None
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
