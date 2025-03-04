"""
A module containing core classes and functions that are used by other modules in the package.
"""

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Optional, Protocol, TypeVar

from src.performance import measure_task_performance

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
    Convert data into video format, using a specified encoding.
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
    enable_parallelization: bool = False
    frames_per_second: int = 24
    max_workers: Optional[int] = None
    show_decoding_window: bool = False
    verbose: bool = False


@dataclass
class VideoEncodingPipeline:
    """A dataclass representing a video encoding pipeline."""

    encoding_function: EncodingFunction
    decoding_function: DecodingFunction
    configuration: VideoEncodingConfiguration
    serialize_function: Optional[SerializeFunction] = None
    deserialize_function: Optional[DeserializeFunction] = None
    processing_function: Optional[ProcessingFunction] = None

    def run_encode(self, data: Any, video_file_path: str) -> None:
        """
        Runs the encoding part of the pipeline.
        """

        if self.serialize_function:
            data = self.serialize_function(data)

        if self.processing_function is not None:
            # TODO: Add processing function.
            # serialized_data = self.processing_function(serialized_data)
            raise NotImplementedError("Processing function is not implemented.")

        if self.configuration.verbose:
            print("\nEncoding...")

            duration = measure_task_performance(
                partial(
                    self.encoding_function, data, video_file_path, self.configuration
                )
            )

            print(f"\nFinished encoding in {duration:.4f} seconds.")
        else:
            self.encoding_function(data, video_file_path, self.configuration)

    def run_decode(self, video_file_path: str) -> T:
        """
        Runs the decoding part of the pipeline.
        """

        if self.configuration.verbose:
            print("\nDecoding...")

            data, duration = measure_task_performance(
                partial(self.decoding_function, video_file_path, self.configuration)
            )

            print(f"\nFinished decoding in {duration:.4f} seconds.\n")
        else:
            data = self.decoding_function(video_file_path, self.configuration)

        if self.deserialize_function:
            data = self.deserialize_function(data)

        return data

    def run_pipeline(self, data: T, video_file_path: str) -> T:
        """
        Runs the full pipeline, making a roundtrip.
        """

        if self.configuration.verbose:
            print("--- Running QR encoding pipeline ---\n")

        self.run_encode(data, video_file_path)

        data = self.run_decode(video_file_path)

        if self.configuration.verbose:
            print("--- Finished QR encoding pipeline ---\n")

        return data
