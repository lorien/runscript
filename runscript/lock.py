"""Provide functions for check if file is locked."""

import logging
import os
import os.path
import sys
from typing import BinaryIO

if os.name != "nt":
    from fcntl import LOCK_EX, LOCK_NB, flock
else:
    import portalocker  # pylint: disable=import-error

LOG = logging.getLogger("runscript.lock")
LOCKS = {}


class LockFileError(Exception):
    pass


class UnsupportedPlatform(Exception):
    pass


def lock_file_nt(file: BinaryIO) -> None:
    try:
        portalocker.lock(
            file, portalocker.LockFlags.EXCLUSIVE | portalocker.LockFalgs.NON_BLOCKING
        )
    except portalocker.LockException as ex:
        raise LockFileError from ex


def lock_file_posix(file: BinaryIO) -> None:
    try:
        flock(file.fileno(), LOCK_EX | LOCK_NB)
    except OSError as ex:
        raise LockFileError from ex


def set_lock(fname: str) -> bool:
    """
    Try to lock file and write PID.

    Return the status of operation.
    """
    # pylint: disable=consider-using-with
    file = open(fname, "wb")  # noqa: SIM115
    # save reference to file handler so that GC does not close it
    # when function execution ends
    LOCKS[fname] = file

    try:
        if os.name == "nt":
            lock_file_nt(file)
        elif os.name == "posix":
            lock_file_posix(file)
        else:
            raise UnsupportedPlatform(
                "Unsupported operating system: {}".format(os.name)
            )
    except LockFileError:
        return False
    file.write(str(os.getpid()).encode())
    file.flush()
    return True


def assert_lock(fname: str) -> None:
    """If file is locked then terminate program else lock file."""
    if not set_lock(fname):
        LOG.error(
            "Terminating current process because file %s is already locked.", fname
        )
        sys.exit()
