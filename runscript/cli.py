import os
from argparse import ArgumentParser
import logging
import sys 
import imp

from runscript.lock import assert_lock
#from runscript.config import load_config
#from grab.util.py3k_support import *

logger = logging.getLogger('runscript.cli')
PY3K = False

def activate_env(env_path):
    activate_script = os.path.join(env_path, 'bin/activate_this.py')
    # py3 hack
    if PY3K:
        exec(compile(open(activate_script).read(), activate_script, 'exec'),
             dict(__file__=activate_script))
    else:
        execfile(activate_script, dict(__file__=activate_script))


def setup_logging(action, level, clear_handlers=False):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    if clear_handlers:
        for hdl in root.handlers:
            root.removeHandler(hdl)

    hdl = logging.StreamHandler()
    hdl.setLevel(level)
    root.addHandler(hdl)


def process_env_option():
    parser = ArgumentParser()
    parser.add_argument('--env')
    args, trash = parser.parse_known_args()
    if args.env:
        activate_env(args.env)


def module_is_importable(path):
    mod_names = path.split('.')
    mod = None
    for mod_name in mod_names:
        if mod is None:
            path = None
        else:
            path = mod.__path__
        try:
            mod_file, mod_path, mod_info = imp.find_module(mod_name, path)
        except ImportError:
            return False
        else:
            mod = imp.load_module(mod_name, mod_file, mod_path, mod_info)
    return True


def process_command_line():
    # Add current directory to python path
    cur_dir = os.path.realpath(os.getcwd())
    sys.path.insert(0, cur_dir)

    process_env_option()

    parser = ArgumentParser()
    parser.add_argument('action', type=str)
    parser.add_argument('--logging-level', default='debug')
    #parser.add_argument('--lock-key')
    #parser.add_argument('--ignore-lock', action='store_true', default=False)
    parser.add_argument('--settings', type=str, default='settings')
    parser.add_argument('--env', type=str)
    parser.add_argument('--profile', action='store_true', default=False)

    args, trash = parser.parse_known_args()

    # Disable django DEBUG feature to prevent memory leaks
    if not 'DJANGO_SETTINGS_MODULE' in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    try:
        from django.conf import settings
    except Exception:
        pass
    else:
        settings.DEBUG = False

    # Setup logging
    logging_level = getattr(logging, args.logging_level.upper())
    #if args.positional_args:
        #command_key = '_'.join([args.action] + args.positional_args)
    #else:
        #command_key = args.action
    setup_logging(args.action, logging_level, clear_handlers=True)

    # Setup action handler
    action_name = args.action

    search_paths = ('grab.script', 'script')
    action_mod = None

    for path in search_paths:
        imp_path = '%s.%s' % (path, action_name)
        if module_is_importable(imp_path):
            action_mod = __import__(imp_path, None, None, ['foo'])

    if action_mod is None:
        sys.stderr.write('Could not find the package to import %s module' % action_name)
        sys.exit(1)

    if hasattr(action_mod, 'setup_arg_parser'):
        action_mod.setup_arg_parser(parser)
    args, trash = parser.parse_known_args()

    # TODO: enable lock-file processing
    #lock_key = None
    #if not args.slave:
        #if not args.ignore_lock:
            #if not args.lock_key:
                #if hasattr(action_mod, 'setup_lock_key'):
                    #lock_key = action_mod.setup_lock_key(action_name, args)
                #else:
                    #lock_key = command_key
            #else:
                #lock_key = args.lock_key
    #if lock_key is not None:
        #lock_path = 'var/run/%s.lock' % lock_key
        #print 'Trying to lock file: %s' % lock_path
        #assert_lock(lock_path)

    #logger.debug('Executing %s action' % action_name)
    try:
        if args.profile:
            import cProfile
            import pyprof2calltree
            import pstats

            profile_file = 'var/%s.prof' % action_name
            profile_tree_file = 'var/%s.prof.out' % action_name

            prof = cProfile.Profile()
            prof.runctx('action_mod.main(**vars(args))',
                        globals(), locals())
            stats = pstats.Stats(prof)
            stats.strip_dirs()
            pyprof2calltree.convert(stats, profile_tree_file)
        else:
            action_mod.main(**vars(args))
    except Exception as ex:
        logging.error('Unexpected exception from action handler:', exc_info=ex)
