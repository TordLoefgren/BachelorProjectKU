"""
A module containing utility functions that are used by other modules in the package.
"""

import base64
import os
import struct
from pathlib import Path
from random import choice, randbytes
from string import ascii_uppercase
from tkinter import filedialog
from typing import Any, Optional, Type

import numpy as np
from src.constants import ALLOWED_TYPES, PROJECT_DIRECTORY, UTF_8_ENCODING_STRING

# region ----- Serialization -----


def to_bytes(data: ALLOWED_TYPES) -> bytes:
    """
    Returns the byte representation of the given data.
    """

    match data:
        case bytes():
            return data
        case str():
            return data.encode(UTF_8_ENCODING_STRING)
        case int() | float():
            return struct.pack("d", data)
        case np.ndarray():
            return data.tobytes()
        case _:
            raise TypeError(f"Unsupported data type: {type(data)}.")


def from_bytes(data: bytes, data_type: Optional[Type[ALLOWED_TYPES]] = None) -> Any:
    """
    Returns the data represented by the bytes.
    """

    if not isinstance(data, bytes):
        raise TypeError(f"Unsupported data type: {type(data)}")

    if data_type is None:
        data_type = str()

    match data_type:
        case bytes():
            return data
        case str():
            return data.decode(UTF_8_ENCODING_STRING)
        case int() | float():
            return struct.unpack("d", data)
        case np.ndarray:
            return np.frombuffer(data)
        case _:
            raise TypeError(f"Unsupported data type: {type(data)}")


def to_base64(data: Any) -> str:
    """
    Base64-encodes the given data.

    If the data is not in bytes, we first convert it to bytes.
    """

    if not isinstance(data, bytes):
        data = to_bytes(data)

    encoded_data = base64.b64encode(data)

    return encoded_data.decode(UTF_8_ENCODING_STRING)


def from_base64(data: str, decode_as_string: bool = False) -> Any:
    """
    Base64-decodes the given data.

    If the decoded data is expected to be a string, we first 'utf-8' decode the the data.
    """

    decoded_bytes = base64.b64decode(data)

    if decode_as_string:
        return decoded_bytes.decode(UTF_8_ENCODING_STRING)
    else:
        return from_bytes(decoded_bytes)


# endregion


# region ----- Generate data -----


def generate_random_ascii_string(n: int) -> str:
    """
    Generates a string of n random ascii uppercase characters.
    """

    return "".join(choice(ascii_uppercase) for _ in range(n))


def generate_random_bytes(n: int) -> bytes:
    """
    Generates n random bytes.
    """

    return randbytes(n)


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


def bytes_to_display(num_bytes: int, factor: int = 1024) -> str:
    """
    Inspiration from:
    https://stackoverflow.com/questions/1094841/get-a-human-readable-version-of-a-file-size
    """

    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]

    for unit in units:
        if num_bytes < factor:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= factor

    return f"{num_bytes:.2f} YB"


# endregion
