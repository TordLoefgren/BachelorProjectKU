"""
A module containing core classes and functions that are used by other modules in the package.
"""

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any, Optional, Protocol, TypeVar

from src.performance import measure_task_performance

PROJECT_DIRECTORY = Path(__file__).parent.parent
UTF_8_ENCODING_STRING = "utf-8"

T = TypeVar("T")


class PipelineValidationException(Exception):
    pass


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
        configuration: "EncodingConfiguration",
    ) -> None:
        pass


class DecodingFunction(Protocol):
    """
    Convert the video back into the original data format.
    """

    def __call__(
        self,
        video_file_path: str,
        configuration: "EncodingConfiguration",
    ) -> bytes:
        pass


class DeserializeFunction(Protocol):
    """
    Deserialize the decoded data.
    """

    def __call__(self, data: bytes) -> T:
        pass


class ProcessingFunction(Protocol):
    """
    Process the data in some way that emulates what a video service might do.
    """

    def __call__(self, data: bytes) -> bytes:
        pass


class ValidationFunction(Protocol):
    """
    Validates the result of the pipeline run by comparing its input and output by a some metric.
    """

    def __call__(self, input: bytes, output: bytes) -> bool:
        pass


@dataclass
class EncodingConfiguration:
    enable_parallelization: bool = False
    frames_per_second: int = 24
    show_decoding_window: bool = False
    verbose: bool = False
    chunk_size: Optional[int] = None
    max_workers: Optional[int] = None


@dataclass
class VideoEncodingPipeline:
    """A dataclass representing a video encoding pipeline."""

    encoding_function: EncodingFunction
    decoding_function: DecodingFunction
    configuration: EncodingConfiguration
    serialize_function: Optional[SerializeFunction] = None
    deserialize_function: Optional[DeserializeFunction] = None
    processing_function: Optional[ProcessingFunction] = None
    validation_function: Optional[ValidationFunction] = None

    def run_encode(self, data: Any, video_file_path: str) -> None:
        """
        Runs the encoding part of the pipeline.
        """

        if self.serialize_function is not None:
            data = self.serialize_function(data)

        if self.processing_function is not None:
            data = self.processing_function(data)

        if self.configuration.verbose:
            print(f"Encoding {len(data)} bytes...")

            duration = measure_task_performance(
                partial(
                    self.encoding_function, data, video_file_path, self.configuration
                )
            )

            print(f"\nEncoding finished in {duration:.4f} seconds.")
        else:
            self.encoding_function(data, video_file_path, self.configuration)

    def run_decode(self, video_file_path: str) -> T:
        """
        Runs the decoding part of the pipeline.
        """

        if self.configuration.verbose:
            print("\nDecoding...")

            result, duration = measure_task_performance(
                partial(self.decoding_function, video_file_path, self.configuration)
            )

            print(f"\nDecoding finished in {duration:.4f} seconds.\n")
        else:
            result = self.decoding_function(video_file_path, self.configuration)

        if self.deserialize_function is not None:
            result = self.deserialize_function(result)

        return result

    def run(self, data: T, video_file_path: str) -> T:
        """
        Runs the full pipeline, making a roundtrip.
        """

        verbose = self.configuration.verbose

        if verbose:
            print("--- Running QR encoding pipeline ---\n")

        self.run_encode(data, video_file_path)

        result = self.run_decode(video_file_path)

        if verbose:
            print("--- Finished QR encoding pipeline ---\n")

        if self.validation_function is not None and not self.validation_function(
            data, result
        ):
            raise PipelineValidationException(
                "The decoded data does not match the encoded data. "
            )

        return result
