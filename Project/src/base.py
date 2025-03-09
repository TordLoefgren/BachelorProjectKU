"""
A module containing core classes and functions that are used by other modules in the package.
"""

from dataclasses import dataclass
from typing import Any, Callable, Optional

from src.constants import T, TFrames
from src.utils import bytes_to_display


class PipelineValidationException(Exception):
    pass


@dataclass
class EncodingConfiguration:
    enable_parallelization: bool = False
    frames_per_second: int = 24
    show_decoding_window: bool = False
    verbose: bool = False
    chunk_size: Optional[int] = None
    max_workers: Optional[int] = None


SerializeFunction = Callable[[T], bytes]
DeserializeFunction = Callable[[bytes], T]

EncodeFunction = Callable[[bytes, EncodingConfiguration], TFrames]
DecodeFunction = Callable[[TFrames, EncodingConfiguration], bytes]

WriteVideoFunction = Callable[[TFrames, str, EncodingConfiguration], None]
ReadVideoFunction = Callable[[str, EncodingConfiguration], TFrames]

ValidateFunction = Callable[[bytes, bytes], bool]


def validate_equal_size(input: bytes, output: bytes) -> bool:
    return len(input) == len(output)


@dataclass
class VideoEncodingPipeline:
    """A dataclass representing a video encoding pipeline."""

    encode_function: EncodeFunction
    decode_function: DecodeFunction
    write_video_function: WriteVideoFunction
    read_video_function: ReadVideoFunction
    serialize_function: Optional[SerializeFunction] = None
    deserialize_function: Optional[DeserializeFunction] = None
    validate_function: Optional[ValidateFunction] = None

    def run_encode(
        self, data: Any, video_file_path: str, configuration: EncodingConfiguration
    ) -> None:
        """
        Runs the encoding part of the pipeline.
        """

        if self.serialize_function is not None:
            data = self.serialize_function(data)

        if configuration.verbose:
            print(f"Encoding {bytes_to_display(len(data))}...")

        frames = self.encode_function(data, configuration)

        self.write_video_function(frames, video_file_path, configuration)

    def run_decode(
        self, video_file_path: str, configuration: EncodingConfiguration
    ) -> T:
        """
        Runs the decoding part of the pipeline.
        """

        frames = self.read_video_function(video_file_path, configuration)

        if configuration.verbose:
            print("\nDecoding...")

        result = self.decode_function(frames, configuration)

        if self.deserialize_function is not None:
            result = self.deserialize_function(result)

        return result

    def run(
        self, data: T, video_file_path: str, configuration: EncodingConfiguration
    ) -> T:
        """
        Runs the full pipeline, making a roundtrip.
        """

        verbose = configuration.verbose

        if verbose:
            print("--- Running pipeline ---\n")

        self.run_encode(data, video_file_path, configuration)

        result = self.run_decode(video_file_path, configuration)

        if verbose:
            print("\n--- Finished pipeline ---\n")

        if self.validate_function is not None and not self.validate_function(
            data, result
        ):
            raise PipelineValidationException(
                "The decoded data does not match the encoded data. "
            )

        return result
