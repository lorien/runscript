"""Provide functions for check if file is locked."""

import logging
import os
import os.path
import sys
from typing import BinaryIO

LOG = logging.getLogger("runscript.lock")
LOCKS = {}


class LockFailed(Exception):
    pass


def lock_windows_file_handler(file_handler: BinaryIO) -> None:
    # Code for NT systems got from: http://code.activestate.com/recipes/65203/
    # pylint: disable=import-outside-toplevel,import-error
    import pywintypes  # type: ignore
    import win32con  # type: ignore
    import win32file  # type: ignore

    const_lock_ex = win32con.LOCKFILE_EXCLUSIVE_LOCK
    const_lock_nb = win32con.LOCKFILE_FAIL_IMMEDIATELY

    # is there any reason not to reuse the following structure?
    __overlapped = pywintypes.OVERLAPPED()

    hfile = win32file._get_osfhandle(  # pylint: disable=protected-access
        file_handler.fileno()
    )
    try:
        win32file.LockFileEx(
            hfile, const_lock_ex | const_lock_nb, 0, -0x10000, __overlapped
        )
    except pywintypes.error as ex:
        # error: (33, 'LockFileEx', 'The process cannot access
        # the file because another process has locked a portion
        # of the file.')
        if ex[0] == 33:
            raise LockFailed from ex


def lock_unix_file_handler(file_handler: BinaryIO) -> None:
    # pylint: disable=import-outside-toplevel
    from fcntl import LOCK_EX, LOCK_NB, flock

    try:
        flock(file_handler.fileno(), LOCK_EX | LOCK_NB)
    except Exception as ex:
        raise LockFailed from ex


def set_lock(fname: str) -> bool:
    """
    Try to lock file and write PID.

    Return the status of operation.
    """
    # pylint: disable=consider-using-with
    file_handler = open(fname, "wb")  # noqa: SIM115
    # save reference to lock file handle to not close it
    # when function execution ends
    LOCKS[fname] = file_handler

    try:
        if os.name == "nt":
            lock_windows_file_handler(file_handler)
        else:
            lock_unix_file_handler(file_handler)
    except LockFailed:
        return False
    file_handler.write(str(os.getpid()).encode())
    file_handler.flush()
    return True


def assert_lock(fname: str) -> None:
    """If file is locked then terminate program else lock file."""
    if not set_lock(fname):
        LOG.error(
            "Terminating current process because file %s is already locked.", fname
        )
        sys.exit()
