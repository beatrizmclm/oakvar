from .issue import issue
from .run import run
from .report import report
from .test import test as do_test
from . import new
from . import store
from . import config
from . import module

_ = issue or run or report or do_test or config or module or new or store


def version():
    """version."""
    from ..lib.util.admin_util import oakvar_version

    ret = oakvar_version()
    return ret


def handle_exception(e: Exception):
    """handle_exception.

    Args:
        e (Exception): e
    """
    from sys import stderr
    from traceback import print_exc
    from ..lib.exceptions import ExpectedException
    import sys

    msg = getattr(e, "msg", None)
    if msg:
        stderr.write(msg)
        stderr.write("\n")
        stderr.flush()
    trc = getattr(e, "traceback", None)
    if trc:
        print_exc()
    isatty = hasattr(sys, "ps1")  # interactive shell?
    halt = getattr(e, "halt", False)
    returncode = getattr(e, "returncode", 1)
    if hasattr(e, "traceback") and getattr(e, "traceback"):
        import traceback

        traceback.print_exc()
    if isinstance(e, ExpectedException):
        if halt:
            if isatty:
                return False
            else:
                exit(returncode)
        else:
            if isatty:
                return False
            else:
                return False
    elif isinstance(e, KeyboardInterrupt):
        pass
    else:
        raise e
