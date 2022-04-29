"""base stuff with no further dependency within pomalevi"""

import builtins
import os.path
import typing as tg

Stoptimes = tg.List[tg.List[float]]

verbose = False


def open(dirlist: tg.Sequence[str], filename: str, mode: str):
    """Open filename as is or in any of the given dirs."""
    if os.path.exists(filename):
        return open(filename, mode)
    for dir in dirlist:
        fullname = f"{dir}/{filename}"
        if os.path.exists(fullname):
            return builtins.open(fullname, mode)
    return open(filename, mode)  # fail like a vanilla open() would


def find(dirlist: tg.Sequence[str], filename: str) -> str:
    if os.path.exists(filename):
        return filename
    for dir in dirlist:
        fullname = f"{dir}/{filename}"
        if os.path.exists(fullname):
            return fullname
    return ''  # not found


def trace(cmd):
    if verbose:
        print("### ", cmd)        