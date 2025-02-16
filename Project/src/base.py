"""
A file containing functions and classes that are used by other parts of the package.
"""

import base64
from dataclasses import dataclass
from enum import Enum, unique
from pathlib import Path
from random import choice
from string import ascii_uppercase
from typing import Any, Callable, Dict, Optional

UTF_8_ENCODING_STRING = "utf-8"


def read_file_as_binary(file_path: Path) -> bytes:
    """
    Attempts to read the binary content of the given file path.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found.")

    with open(file_path, mode="rb") as f:
        return f.read()


def to_base64(data: Any) -> str:
    """
    Base64-encodes the given data.

    If the data is a string, we first 'utf-8' encode the the data.
    """
    if isinstance(data, str):
        data = data.encode(UTF_8_ENCODING_STRING)
    encoded_data = base64.b64encode(data)

    return encoded_data.decode(UTF_8_ENCODING_STRING)


def from_base64(data: str, is_string: bool = False) -> Any:
    """
    Base64-decodes the given data.

    If the decoded data is expected to be a string, we first 'utf-8' decode the the data.
    """
    decoded_data = base64.b64decode(data)

    if is_string:
        return decoded_data.decode(UTF_8_ENCODING_STRING)

    return decoded_data


def generate_random_string(n: int) -> str:
    """
    Generates a string of n random ascii uppercase characters.
    """

    return "".join(choice(ascii_uppercase) for _ in range(n))


# region ------------ WIP and ideas section ------------


FILE_PATH: Path = Path(__file__).resolve()
TEST_DATA_DIRECTORY: Path = FILE_PATH.parent.parent / "tests" / "test_data"

AUDIO_TEST_FILE = "test_audio.mp3"
TEXT_TEST_FILE = "test_text.txt"
VIDEO_TEST_FILE = "test_video.mp4"


# Prepare the test data (text, video, or sound).
PreparationFunction = Callable[..., Any]

# Convert test data into video format, using a specified encoding.
EncodingFunction = Callable[..., Any]

# Process the data in some way that emulates what a video service might do (Optional).
ProcessingFunction = Callable[..., Any]

# Convert the video back into the original data format.
DecodingFunction = Callable[..., Any]


@dataclass
class TestCasePipeline:
    """A dataclass representing a test case pipeline."""

    name: str
    prepare: PreparationFunction
    encode: EncodingFunction
    decode: DecodingFunction
    process: Optional[ProcessingFunction] = None


# TODO: Create enum package file when this enum is in use.
@unique
class FileType(Enum):
    AUDIO = 0
    TEXT = 1
    VIDEO = 2


def get_test_data_lookup() -> Dict[FileType, Path]:
    test_files_lookup = {
        FileType.AUDIO: TEST_DATA_DIRECTORY / AUDIO_TEST_FILE,
        FileType.TEXT: TEST_DATA_DIRECTORY / TEXT_TEST_FILE,
        FileType.VIDEO: TEST_DATA_DIRECTORY / VIDEO_TEST_FILE,
    }

    for file_path in test_files_lookup.values():
        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} not found.")

    return test_files_lookup


# endregion
