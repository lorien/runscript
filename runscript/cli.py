import imp  # pylint: disable=deprecated-module
import logging
import os
import sys
from argparse import ArgumentParser
from traceback import format_exception
from types import ModuleType, TracebackType
from typing import Optional

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
    root = logging.getLogger()
    if clear_handlers:
        for hdl in root.handlers:
            root.removeHandler(hdl)
    root.setLevel(logging.DEBUG)
    hdl = logging.StreamHandler()
    hdl.setLevel(logging.DEBUG)
    root.addHandler(hdl)


def is_importable_module(path: str) -> bool:
    mod_names = path.split(".")
    wtf = None
    for mod_name in mod_names:
        try:
            _, mod_path, _ = imp.find_module(mod_name, wtf)
        except ImportError:
            return False
        else:
            wtf = [mod_path]
    return True


def custom_excepthook(
    etype: type[BaseException], evalue: BaseException, etb: Optional[TracebackType]
) -> None:
    LOG.fatal("\n".join(format_exception(etype, evalue, etb)))


def load_module(locations: list[str], module_name: str) -> ModuleType:
    for path in locations:
        imp_path = "%s.%s" % (path, module_name)
        if is_importable_module(imp_path):
            return __import__(imp_path, None, None, ["foo"])
    raise ModuleNotFound


def process_lock_key(lock_key: str) -> None:
    lock_path = "var/run/%s.lock" % lock_key
    LOG.debug("Locking file: %s", lock_path)
    assert_lock(lock_path)


def process_command_line() -> None:
    # Use custom excepthook that prints traceback via logging system
    # using FATAL level
    sys.excepthook = custom_excepthook
    # Add current directory to python path
    sys.path.insert(0, os.path.realpath(os.getcwd()))
    parser = ArgumentParser(allow_abbrev=False)
    parser.add_argument("action", type=str)
    parser.add_argument("--lock-key")
    opts, _ = parser.parse_known_args()
    config = DEFAULT_CONFIG
    setup_logging(clear_handlers=True)
    # Setup action handler
    try:
        script_module = load_module(config["global"]["search_path"], opts.action)
    except ModuleNotFound:
        sys.stderr.write("Could not find or load module: {}\n".format(opts.action))
        sys.exit(1)
    if hasattr(script_module, "setup_arg_parser"):
        script_module.setup_arg_parser(parser)
    opts, _ = parser.parse_known_args()
    # Update proc title
    if hasattr(script_module, "get_proc_title"):
        setproctitle(script_module.get_proc_title(opts))
    else:
        setproctitle("run_%s" % opts.action)
    func_args = vars(opts)
    if hasattr(script_module, "get_lock_key"):
        func_args["lock_key"] = script_module.get_lock_key(**func_args)
    if func_args["lock_key"]:
        process_lock_key(func_args["lock_key"])
    script_module.main(**func_args)


if __name__ == "__main__":
    process_command_line()
