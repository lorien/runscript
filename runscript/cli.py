import logging
import os
import sys
from argparse import ArgumentParser, Namespace
from importlib import import_module
from importlib.util import find_spec
from traceback import format_exception
from types import ModuleType, TracebackType
from typing import Optional, cast

from setproctitle import setproctitle

from runscript.lock import assert_lock

DEFAULT_CONFIG = {
    "global": {
        "search_path": ["script"],
    },
}
LOG = logging.getLogger(__name__)


class ModuleNotFound(Exception):
    pass


def setup_logging(clear_handlers: bool = False) -> None:
    root_logger = logging.getLogger()
    if clear_handlers:
        for hdl in root_logger.handlers:
            root_logger.removeHandler(hdl)
    root_logger.setLevel(logging.DEBUG)
    hdl = logging.StreamHandler()
    hdl.setLevel(logging.DEBUG)
    root_logger.addHandler(hdl)


def custom_excepthook(
    etype: type[BaseException], evalue: BaseException, etb: Optional[TracebackType]
) -> None:
    LOG.fatal("\n".join(format_exception(etype, evalue, etb)))


def locate_module(locations: list[str], module_name: str) -> ModuleType:
    for path in locations:
        imp_path = "%s.%s" % (path, module_name)
        if find_spec(imp_path):
            return import_module(imp_path)
    raise ModuleNotFound


def process_lock_key(lock_key: str) -> None:
    lock_path = "var/run/%s.lock" % lock_key
    LOG.debug("Locking file: %s", lock_path)
    assert_lock(lock_path)


def update_process_title(script_module: ModuleType, opts: Namespace) -> None:
    if hasattr(script_module, "get_proc_title"):
        title = script_module.get_proc_title(opts)
    else:
        title = "run_{}".format(opts.action)
    setproctitle(title)


def process_lock(script_module: ModuleType, opts: Namespace) -> Optional[str]:
    if hasattr(script_module, "get_lock_key"):
        lock_key = script_module.get_lock_key(opts)
    else:
        lock_key = opts.lock_key
    if lock_key:
        process_lock_key(lock_key)
    return cast(Optional[str], lock_key)


def process_main_cli_args(parser: ArgumentParser) -> Namespace:
    parser.add_argument("action", type=str)
    parser.add_argument("--lock-key", type=str)
    opts, _ = parser.parse_known_args()
    return opts


def parse_script_cli_args(
    parser: ArgumentParser, script_module: ModuleType
) -> Namespace:
    if hasattr(script_module, "setup_arg_parser"):
        script_module.setup_arg_parser(parser)
    opts, _ = parser.parse_known_args()
    return opts


def process_command_line() -> None:
    setup_logging(clear_handlers=True)
    # Use custom excepthook that prints traceback via logging system
    # using FATAL level
    sys.excepthook = custom_excepthook
    # Add current directory to python path
    # to make working all imports from local packages which are not installed
    # to site-packages
    sys.path.insert(0, os.path.realpath(os.getcwd()))
    parser = ArgumentParser(allow_abbrev=False)
    opts = process_main_cli_args(parser)
    try:
        script_module = locate_module(
            DEFAULT_CONFIG["global"]["search_path"], opts.action
        )
    except ModuleNotFound:
        sys.stderr.write("Could not find or load module: {}\n".format(opts.action))
        sys.exit(1)
    opts = parse_script_cli_args(parser, script_module)
    update_process_title(script_module, opts)
    func_args = vars(opts)
    func_args["lock_key"] = process_lock(script_module, opts)
    script_module.main(**func_args)


if __name__ == "__main__":
    process_command_line()
