"""
A module containing core classes and functions that are used by other modules in the package.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Protocol, TypeVar

PROJECT_DIRECTORY = Path(__file__).parent
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
