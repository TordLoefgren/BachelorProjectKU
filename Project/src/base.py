"""
A module containing core classes and functions that are used by other modules in the package.
"""

import base64
import pickle
import struct
from dataclasses import dataclass
from pathlib import Path
from random import choice, randbytes
from string import ascii_uppercase
from typing import Any, Optional, Protocol, TypeVar

import numpy as np

UTF_8_ENCODING_STRING = "utf-8"

T = TypeVar("T")


class SerializeFunction(Protocol):
    """
    Serialize the raw data.
    """

    def __call__(self, data: T) -> bytes:
        pass


class EncodingFunction(Protocol):
    """
    Convert test data into video format, using a specified encoding.
    """

    def __call__(
        self,
        serialized_data: bytes,
        video_file_path: str,
        configuration: "VideoEncodingConfiguration",
    ) -> None:
        pass


class ProcessingFunction(Protocol):
    """
    Process the data in some way that emulates what a video service might do.
    """

    def __call__(self, data: bytes) -> bytes:
        pass


class DecodingFunction(Protocol):
    """
    Convert the video back into the original data format.
    """

    def __call__(
        self,
        video_file_path: str,
        configuration: "VideoEncodingConfiguration",
    ) -> bytes:
        pass


class DeserializeFunction(Protocol):
    """
    Deserialize the decoded data.
    """

    def __call__(self, data: bytes) -> T:
        pass


@dataclass
class VideoEncodingConfiguration:
    frames_per_second: int = 24
    show_decoding_window: bool = False


@dataclass
class VideoEncodingPipeline:
    """A dataclass representing a video encoding pipeline."""

    serialize_function: SerializeFunction
    encoding_function: EncodingFunction
    decoding_function: DecodingFunction
    deserialize_function: DeserializeFunction
    configuration: VideoEncodingConfiguration
    processing_function: Optional[ProcessingFunction] = None

    def run_encode(self, data: Any, video_file_path: str) -> None:
        """
        Runs the encoding part of the pipeline.
        """

        serialized_data = self.serialize_function(data)

        if self.processing_function is not None:
            serialized_data = self.processing_function(serialized_data)

        self.encoding_function(serialized_data, video_file_path, self.configuration)

    def run_decode(self, video_file_path: str) -> T:
        """
        Runs the decoding part of the pipeline.
        """

        decoded_data = self.decoding_function(video_file_path, self.configuration)

        return self.deserialize_function(decoded_data)

    def run_pipeline(self, data: T, video_file_path: str) -> T:
        """
        Runs the full pipeline, making a roundtrip.
        """

        self.run_encode(data, video_file_path)

        return self.run_decode(video_file_path)


def read_file_as_binary(file_path: Path) -> bytes:
    """
    Attempts to read the binary content of the given file path.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} not found.")

    with open(file_path, mode="rb") as f:
        return f.read()


def to_bytes(data: Any) -> bytes:
    """
    Returns the byte representation of the given data.

    Inspiration from:
    https://stackoverflow.com/questions/62565944/how-to-convert-any-object-to-a-byte-array-and-keep-it-on-memory
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
            # Collections and objects.
            try:
                return pickle.dumps(data)
            except Exception as e:
                raise TypeError(f"Unsupported data type: {type(data)}") from e


def from_bytes(data: bytes) -> Any:
    """
    Returns the data represented by the bytes.
    """

    if not isinstance(data, bytes):
        raise TypeError(f"Unsupported data type: {type(data)}")

    # TODO: Create decoding for types like in to_bytes.

    return data.decode(UTF_8_ENCODING_STRING)


def generate_random_string(n: int) -> str:
    """
    Generates a string of n random ascii uppercase characters.
    """

    return "".join(choice(ascii_uppercase) for _ in range(n))


def generate_bytes(n: int) -> bytes:
    """
    Generates n random bytes.
    """

    return randbytes(n)


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


# region ----- WIP and ideas section -----

# endregion
