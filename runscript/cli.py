import os
import sys
import imp
import logging

try:
    from ConfigParser import RawConfigParser, NoOptionError
except ImportError:
    from configparser import RawConfigParser, NoOptionError

from argparse import ArgumentParser
from traceback import format_exception
from setproctitle import setproctitle

from runscript.lock import assert_lock


logger = logging.getLogger("runscript.cli")


def setup_logging(action, level, clear_handlers=False):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    if clear_handlers:
        for hdl in root.handlers:
            root.removeHandler(hdl)

    hdl = logging.StreamHandler()
    hdl.setLevel(level)
    root.addHandler(hdl)


def module_is_importable(path):
    mod_names = path.split(".")
    path = None
    for mod_name in mod_names:
        try:
            mod_file, mod_path, mod_info = imp.find_module(mod_name, path)
        except ImportError:
            return False
        else:
            path = [mod_path]
    return True


def normalize_config_value(section, name, value):
    if section == "global" and name == "search_path":
        return [x.strip() for x in value.split(",")]
    else:
        return value


def load_config():
    cur_dir = os.getcwd()
    config_path = os.path.join(cur_dir, "run.ini")

    config = {
        "global": {
            "search_path": ["grab.script", "script"],
        },
    }

    if os.path.exists(config_path):
        parser = RawConfigParser()
        parser.read(config_path)
        for section in parser.sections():
            if not section in config:
                config[section] = {}
            for key, val in parser.items(section):
                config[section][key] = normalize_config_value(section, key, val)

    return config


def custom_excepthook(etype, evalue, etb):
    logging.fatal("\n".join(format_exception(etype, evalue, etb)))


def setup_arg_parser():
    parser = ArgumentParser()
    parser.add_argument("action", type=str)
    parser.add_argument("--logging-level", default="debug")
    parser.add_argument("--lock-key")
    # parser.add_argument('--ignore-lock', action='store_true', default=False)
    parser.add_argument("--env", type=str)
    parser.add_argument("--profile", action="store_true", default=False)

    return parser


def global_setup(args):
    # Use custom excepthook that prints traceback via logging system
    # using FATAL level
    sys.excepthook = custom_excepthook

    # Add current directory to python path
    cur_dir = os.path.realpath(os.getcwd())
    sys.path.insert(0, cur_dir)

    logging_level = getattr(logging, args.logging_level.upper())
    setup_logging(args.action, logging_level, clear_handlers=True)


def config_django_settings(args, config):
    if config["global"].get("django_settings_module"):
        os.environ["DJANGO_SETTINGS_MODULE"] = config["global"][
            "django_settings_module"
        ]

        # Disable django DEBUG feature to prevent memory leaks
        import django
        from django.conf import settings

        settings.DEBUG = False

        django.setup()


def setup_import_paths(args, config, parser=None):
    # Setup action handler
    action_name = args.action
    action_mod = None

    for path in config["global"]["search_path"]:
        imp_path = "%s.%s" % (path, action_name)
        if module_is_importable(imp_path):
            action_mod = __import__(imp_path, None, None, ["foo"])
    else:
        # If search path is blank, try to invoke
        # script directly, without namespaces
        if module_is_importable(action_name):
            action_mod = __import__(action_name, None, None, ["foo"])

    if action_mod is None:
        sys.stderr.write(
            "Could not find the package to import %s module\n" % action_name
        )
        sys.exit(1)

    return action_mod


def process_command_line():
    parser = setup_arg_parser()
    args, trash = parser.parse_known_args()
    config = load_config()

    # Configs
    global_setup(args)
    config_django_settings(args, config)
    action_mod = setup_import_paths(args, config, parser=parser)

    # Setup action handler
    action_name = args.action

    if hasattr(action_mod, "setup_arg_parser"):
        action_mod.setup_arg_parser(parser)

    args_obj, trash = parser.parse_known_args()

    # Update proc title
    if hasattr(action_mod, "get_proc_title"):
        setproctitle(action_mod.get_proc_title(args_obj))
    else:
        setproctitle("run_%s" % args.action)

    args = vars(args_obj)

    for key, val in config.get("script:%s" % action_name, {}).items():
        args[key] = val

    if hasattr(action_mod, "get_lock_key"):
        lock_key = action_mod.get_lock_key(**args)
    else:
        lock_key = args["lock_key"]

    if lock_key is not None:
        lock_path = "var/run/%s.lock" % lock_key
        logging.debug("Trying to lock file: {}".format(lock_path))
        assert_lock(lock_path)

    if args["profile"]:
        import cProfile
        import pyprof2calltree
        import pstats

        profile_file = "var/%s.prof" % action_name
        profile_tree_file = "var/%s.prof.out" % action_name

        prof = cProfile.Profile()
        try:
            prof.runctx("action_mod.main(**args)", globals(), locals())
        finally:
            stats = pstats.Stats(prof)
            stats.strip_dirs()
            pyprof2calltree.convert(stats, profile_tree_file)
    else:
        action_mod.main(**args)


if __name__ == "__main__":
    process_command_line()
