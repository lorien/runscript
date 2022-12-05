import imp  # pylint: disable=deprecated-module
import logging
import os
import sys
from argparse import ArgumentParser
from traceback import format_exception
from types import TracebackType
from typing import Optional

from setproctitle import setproctitle

from runscript.lock import assert_lock

DEFAULT_CONFIG = {
    "global": {
        "search_path": ["script"],
    },
}
LOG = logging.getLogger(__name__)


def setup_logging(clear_handlers: bool = False) -> None:
    root = logging.getLogger()
    if clear_handlers:
        for hdl in root.handlers:
            root.removeHandler(hdl)
    root.setLevel(logging.DEBUG)
    hdl = logging.StreamHandler()
    hdl.setLevel(logging.DEBUG)
    root.addHandler(hdl)


def module_is_importable(path: str) -> bool:
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


def process_command_line() -> None:
    # Use custom excepthook that prints traceback via logging system
    # using FATAL level
    sys.excepthook = custom_excepthook
    # Add current directory to python path
    cur_dir = os.path.realpath(os.getcwd())
    sys.path.insert(0, cur_dir)
    parser = ArgumentParser()
    parser.add_argument("action", type=str)
    parser.add_argument("--lock-key")
    known_opts, _ = parser.parse_known_args()
    config = DEFAULT_CONFIG
    setup_logging(clear_handlers=True)
    # Setup action handler
    action_name = known_opts.action
    action_mod = None
    for path in config["global"]["search_path"]:
        imp_path = "%s.%s" % (path, action_name)
        if module_is_importable(imp_path):
            action_mod = __import__(imp_path, None, None, ["foo"])
    if action_mod is None:
        sys.stderr.write(
            "Could not find the package to import %s module\n" % action_name
        )
        sys.exit(1)
    if hasattr(action_mod, "setup_arg_parser"):
        action_mod.setup_arg_parser(parser)
    opts, _ = parser.parse_known_args()
    # Update proc title
    if hasattr(action_mod, "get_proc_title"):
        setproctitle(action_mod.get_proc_title(opts))
    else:
        setproctitle("run_%s" % opts.action)
    func_args = vars(opts)
    if hasattr(action_mod, "get_lock_key"):
        lock_key = action_mod.get_lock_key(**func_args)
    else:
        lock_key = func_args["lock_key"]
    if lock_key is not None:
        lock_path = "var/run/%s.lock" % lock_key
        LOG.debug("Locking file: %s", lock_path)
        assert_lock(lock_path)
    action_mod.main(**func_args)


if __name__ == "__main__":
    process_command_line()
