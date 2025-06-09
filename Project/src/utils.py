"""
A module containing utility functions that are used by other modules in the package.
"""

import os
import random
from itertools import tee
from pathlib import Path
from string import ascii_uppercase
from tkinter import filedialog
from typing import Iterator, Optional, Tuple

import psutil
from src.constants import PROJECT_DIRECTORY

# region ----- Generate data -----


def generate_random_ascii_string(n: int) -> str:
    """
    Generates a string of n random ascii uppercase characters.
    """

    return "".join(random.choice(ascii_uppercase) for _ in range(n))


def generate_random_bytes(n: int, seed: Optional[int] = None) -> bytes:
    """
    Generates n random bytes.
    """

    if seed is not None:
        random.seed(seed)

    return random.randbytes(n)


# endregion

# region ----- Files -----


def read_file_as_binary(file_path: str, size: Optional[int] = None) -> bytes:
    """
    Attempts to read the binary content of the given file path.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")

    with open(file_path, mode="rb") as f:
        return f.read(size)


def write_file_as_binary(data: bytes, file_path: str) -> None:
    """
    Attempts to write the binary content of the given file path.
    """

    with open(file_path, mode="wb") as f:
        return f.write(data)


def remove_file(file_path: str) -> None:
    """
    Removes the file in the given file path if it exists.
    """

    if os.path.exists(file_path):
        os.remove(file_path)


def get_file_extension(file_path: str) -> str:
    """
    Returns the file extension from the file at the given path.

    Inspiration from:

    https://www.geeksforgeeks.org/how-to-get-file-extension-in-python/
    """

    return Path(file_path).suffix


def open_file_dialog() -> str:
    """
    Opens a file dialog and returns the selected file path.

    Inspiration from:

    https://stackoverflow.com/questions/52868551/select-file-instead-of-just-folder-in-tkinter?rq=3

    and

    https://stackoverflow.com/questions/7994461/choosing-a-file-in-python3?rq=3
    """

    return filedialog.askopenfilename(initialdir=PROJECT_DIRECTORY)


# endregion

# region ----- Miscellaneous -----


def bytes_to_display(num_bytes: int, as_binary: bool = False) -> str:
    """
    Inspiration from:
    https://stackoverflow.com/questions/1094841/get-a-human-readable-version-of-a-file-size
    """

    if as_binary:
        factor = 1024
        units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    else:
        factor = 1000
        units = ["B", "kB", "MB", "GB", "TB", "PB"]

    for unit in units:
        if num_bytes < factor:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= factor

    return f"{num_bytes:.2f} {units[-1]}"


def get_core_specifications() -> Tuple[int, int]:
    """
    Gets the number of logical and physical cores from the executing PC.

    Inspiration from:
    https://stackoverflow.com/questions/1006289/how-to-find-out-the-number-of-cpus-using-python
    """

    physical_cores = psutil.cpu_count(logical=False)
    logical_cores = os.cpu_count()

    return physical_cores, logical_cores


def try_get_iter_count(iterator: Iterator) -> Tuple[bool, int, Iterator]:
    try:
        copy, original = tee(iterator)
        count = sum(1 for _ in copy)
        return True, count, original
    except Exception:
        return (
            False,
            0,
        )


# endregion
