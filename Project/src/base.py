"""
A module containing core classes and functions that are used by other modules in the package.
"""

import base64
from dataclasses import dataclass
from typing import Callable, List, Optional

from src.utils import bytes_to_display, get_core_specifications


class PipelineValidationException(Exception):
    pass


@dataclass
class EncodingConfiguration:
    enable_multiprocessing: bool = True
    frames_per_second: int = 24
    show_decoding_window: bool = False
    verbose: bool = False
    chunk_size: Optional[int] = None
    max_workers: Optional[int] = None


@dataclass
class Result[T]:
    """
    A dataclass that encapsulates the result of an operation.
    """

    value: Optional[T]
    exception: Optional[Exception]

    @property
    def is_valid(self):
        return self.exception is None


@dataclass
class Serializer[TSerialized]:
    """
    A dataclass that encapsulates the serializing logic of the pipeline.
    """

    serialize: Callable[[bytes], TSerialized]
    deserialize: Callable[[TSerialized], bytes]


@dataclass
class Base64Serializer(Serializer):
    """
    A serializer for base64 encoding.
    """

    serialize = base64.b64encode
    deserialize = base64.b64decode


@dataclass
class Encoder[TSerialized, TFrame]:
    """
    A dataclass that encapsulates the encoding logic of the pipeline.
    """

    encode: Callable[[TSerialized, EncodingConfiguration], List[TFrame]]
    decode: Callable[[List[TFrame], EncodingConfiguration], TSerialized]


@dataclass
class VideoHandler[TFrame]:
    """
    A dataclass that encapsulates the video I/O logic of the pipeline.
    """

    write: Callable[[List[TFrame], str, EncodingConfiguration], None]
    read: Callable[[str, EncodingConfiguration], List[TFrame]]


ValidationFunction = Callable[[bytes, bytes], bool]


def validate_equals(input: bytes, output: bytes) -> bool:
    """
    A simple validation function that compares the input and output.
    """

    return input == output


@dataclass
class VideoEncodingPipeline[TFrame]:
    """A dataclass representing a video encoding pipeline."""

    serializer: Serializer
    encoder: Encoder
    video_handler: VideoHandler
    validation_function: ValidationFunction

    def encode(
        self,
        data: bytes,
        configuration: EncodingConfiguration,
        file_path: Optional[str] = None,
    ) -> List[TFrame]:
        """
        Runs the encoding part of the pipeline, including generating a video from frames.
        """

        frames = self._encode(data, configuration)

        if file_path is not None:
            self.video_handler.write(frames, file_path, configuration)

        return frames

    def decode(
        self,
        configuration: EncodingConfiguration,
        file_path: Optional[str] = None,
        frames: Optional[List[TFrame]] = None,
    ) -> bytes:
        """
        Runs the decoding part of the pipeline, including extracting frames from a video.
        """

        if file_path is not None:
            frames = self.video_handler.read(file_path, configuration)
        elif frames is None:
            raise ValueError("Supply either a file path or frames for decoding.")

        return self._decode(frames, configuration)

    def run(
        self,
        input: bytes,
        file_path: str,
        configuration: EncodingConfiguration,
        mock: bool = False,
    ) -> Result[bytes]:
        """
        Runs the full pipeline, making a roundtrip.
        """

        verbose = configuration.verbose
        if verbose:
            self._print_start(configuration, len(input))

        frames = self.encode(input, configuration, file_path if not mock else None)

        if not mock:
            frames = self.video_handler.read(file_path, configuration)

        output = self.decode(configuration, file_path if not mock else None, frames)

        is_valid = self.validation_function(input, output)

        if verbose:
            self._print_stop(is_valid, output_length=len(output))

        if not is_valid:
            return Result(
                value=None,
                exception=PipelineValidationException(
                    "The decoded data does not match the encoded data. "
                ),
            )

        return Result(value=output, exception=None)

    def _encode(
        self, data: bytes, configuration: EncodingConfiguration
    ) -> List[TFrame]:
        """
        Runs the encoding part of the pipeline.
        """

        serialized_data = self.serializer.serialize(data)

        if configuration.verbose:
            print("Encoding...")

        return self.encoder.encode(serialized_data, configuration)

    def _decode(
        self,
        frames: List[TFrame],
        configuration: EncodingConfiguration,
    ) -> bytes:
        """
        Runs the decoding part of the pipeline.
        """

        if configuration.verbose:
            print("\nDecoding...")

        result = self.encoder.decode(frames, configuration)

        deserialized_data = self.serializer.deserialize(result + b"==")

        return deserialized_data

    def _print_start(
        self, configuration: EncodingConfiguration, input_length: int
    ) -> None:
        """
        Prints the pipeline starting information.
        """

        print("│")
        print(f"│ Multiprocessing:     {configuration.enable_multiprocessing}")

        if configuration.enable_multiprocessing:
            physical_cores, logical_cores = get_core_specifications()
            max_processes = (
                configuration.max_workers
                if configuration.max_workers is not None
                else logical_cores
            )

            print(f"│ Physical cores:      {physical_cores}")
            print(f"│ Logical cores:       {logical_cores}")
            print(f"│ Max processes:       {max_processes}")

        print("│")
        print(f"│ Input size:          {bytes_to_display(input_length)}")
        print("│")
        print("└──── Running pipeline ────┐")
        print("                           │\n")

    def _print_stop(self, is_valid: bool, output_length: int) -> None:
        """
        Prints the pipeline stop information.
        """

        print("\n                           │")
        print("┌──── Finished pipeline ───┘")
        print("│")
        print(f"│ Output size:          {bytes_to_display(output_length)}")
        print("│")
        print(f"│ Validation:           {"Success" if is_valid else "Failure"}\n")
