"""
A module containing core classes and functions that are used by other modules in the package.
"""

import base64
import pickle
from dataclasses import dataclass
from itertools import chain
from time import perf_counter
from typing import Callable, Iterator, Optional

from src.constants import BYTE_ORDER_BIG, CONFIGURATION_HEADER_LENGTH_BYTES
from src.utils import bytes_to_display, get_core_specifications, try_get_iter_count


@dataclass
class EncodingConfiguration:
    enable_multiprocessing: bool = True
    frames_per_second: int = 24
    show_decoding_window: bool = False
    verbose: bool = False
    chunk_size: Optional[int] = None
    max_workers: Optional[int] = None

    @staticmethod
    def serialize_with_length_prefix(config: "EncodingConfiguration") -> bytes:
        config_bytes = EncodingConfiguration.to_bytes(config)
        length_bytes = len(config_bytes).to_bytes(
            CONFIGURATION_HEADER_LENGTH_BYTES, byteorder=BYTE_ORDER_BIG
        )
        return length_bytes + config_bytes

    @staticmethod
    def deserialize_with_length_prefix(data: bytes) -> "EncodingConfiguration":
        if len(data) < CONFIGURATION_HEADER_LENGTH_BYTES:
            raise ValueError("Header too short to contain full configuration length.")

        config_length = int.from_bytes(
            data[:CONFIGURATION_HEADER_LENGTH_BYTES], byteorder=BYTE_ORDER_BIG
        )
        if len(data) < CONFIGURATION_HEADER_LENGTH_BYTES + config_length:
            raise ValueError("Header too short to contain full configuration.")

        config_bytes = data[
            CONFIGURATION_HEADER_LENGTH_BYTES : CONFIGURATION_HEADER_LENGTH_BYTES
            + config_length
        ]
        return EncodingConfiguration.from_bytes(config_bytes)

    @staticmethod
    def to_bytes(data) -> bytes:
        return pickle.dumps(data)

    @staticmethod
    def from_bytes(data: bytes) -> "EncodingConfiguration":
        return pickle.loads(data)


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


# region ----- Serialization Layer -----


@dataclass
class Serializer[TSerialized]:
    """
    A dataclass that encapsulates the serializing logic of the pipeline.
    """

    serialize: Callable[[bytes], TSerialized]
    deserialize: Callable[[TSerialized], bytes]


Base64Serializer = Serializer(serialize=base64.b64encode, deserialize=base64.b64decode)

IdentitySerializer = Serializer(
    serialize=lambda b: b,
    deserialize=lambda b: b,
)

Latin1Serializer = Serializer(
    serialize=lambda b: b.decode("latin1").encode("latin1"),
    deserialize=lambda b: b.decode("latin1").encode("latin1"),
)

# endregion

# region ----- Encoding Layer-----


@dataclass
class Encoder[TSerialized, TFrame]:
    """
    A dataclass that encapsulates the encoding logic of the pipeline.
    """

    encode: Callable[[TSerialized, EncodingConfiguration, bool], Iterator[TFrame]]
    decode: Callable[[Iterator[TFrame], Optional[EncodingConfiguration]], TSerialized]


# endregion

# region ----- Video Layer -----


@dataclass
class VideoHandler[TFrame]:
    """
    A dataclass that encapsulates the video I/O logic of the pipeline.
    """

    write: Callable[[Iterator[TFrame], str, EncodingConfiguration], None]
    read: Callable[[str, EncodingConfiguration], Iterator[TFrame]]


# endregion

# region ----- Validation Layer -----

ValidationFunction = Callable[[bytes, bytes], bool]


def validate_equals(input: bytes, output: bytes) -> bool:
    """
    A simple validation function that compares the input and output.
    """

    return input == output


# endregion

# region ----- Pipeline -----


class PipelineValidationException(Exception):
    pass


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
    ) -> Iterator[TFrame]:
        """
        Runs the encoding part of the pipeline, including generating a video from frames.

        The frames are returned.
        """

        if configuration.verbose:
            print("Encoding...")

        # Configuration header.
        header_with_length = EncodingConfiguration.serialize_with_length_prefix(
            configuration
        )
        header_serialized = self.serializer.serialize(header_with_length)
        header_frames = self.encoder.encode(header_serialized, configuration, True)

        success, count, header_frames = try_get_iter_count(header_frames)
        if success and count != 1:
            raise PipelineValidationException(
                "The configuration header must be exactly one frame."
            )

        # Payload.
        payload_serialized = self.serializer.serialize(data)
        payload_frames = self.encoder.encode(payload_serialized, configuration, False)

        total_frames = chain(header_frames, payload_frames)

        if file_path:
            self.video_handler.write(total_frames, file_path, configuration)

        return total_frames

    def decode(
        self,
        configuration: Optional[EncodingConfiguration],
        file_path: Optional[str] = None,
        frames: Optional[Iterator[TFrame]] = None,
    ) -> bytes:
        """
        Runs the decoding part of the pipeline, including extracting frames from a video.
        """

        if configuration is not None and configuration.verbose:
            print("\nDecoding...")

        if file_path:
            frames = self.video_handler.read(file_path, configuration)
        elif frames is None or not frames:
            raise ValueError("Supply either a file path or frames for decoding.")

        try:
            header_frame = next(frames)
        except StopIteration:
            raise ValueError("No frames provided for decoding.")

        raw_header_serialized = self.encoder.decode([header_frame], None)
        raw_header = self.serializer.deserialize(raw_header_serialized)
        configuration = EncodingConfiguration.deserialize_with_length_prefix(raw_header)

        # Payload.
        raw_payload_serialized = self.encoder.decode(frames, configuration)
        return self.serializer.deserialize(raw_payload_serialized)

    def run(
        self,
        data: bytes,
        file_path: str,
        configuration: EncodingConfiguration,
        mock: bool = False,
    ) -> Result[bytes]:
        """
        Runs the full pipeline, making a roundtrip.
        """

        verbose = configuration.verbose
        if verbose:
            start = perf_counter()
            self._print_start(configuration, len(data))

        frames = self.encode(data, configuration, file_path if not mock else None)

        if not mock:
            frames = self.video_handler.read(file_path, configuration)

        try:
            output = self.decode(configuration, file_path if not mock else None, frames)
        except ValueError as exception:
            return Result(None, exception=exception)

        is_valid = self.validation_function(data, output)

        if verbose:
            duration = perf_counter() - start
            self._print_stop(is_valid, output_length=len(output), duration=duration)

        if not is_valid:
            return Result(
                value=None,
                exception=PipelineValidationException(
                    "The decoded data does not match the encoded data. "
                ),
            )

        return Result(value=output, exception=None)

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
            max_workers = (
                str(configuration.max_workers)
                if configuration.max_workers is not None
                else "Automatic"
            )

            print(f"│ Physical cores:      {physical_cores}")
            print(f"│ Logical cores:       {logical_cores}")
            print(f"│ Max workers:         {max_workers}")

        print("│")
        print(f"│ Input size:          {bytes_to_display(input_length)}")
        print("│")
        print("└──── Running pipeline ────┐")
        print("                           │\n")

    def _print_stop(self, is_valid: bool, output_length: int, duration: float) -> None:
        """
        Prints the pipeline stop information.
        """

        print("\n                           │")
        print("┌──── Finished pipeline ───┘")
        print("│")
        print(f"│ Output size:          {bytes_to_display(output_length)}")
        print(f"│ Duration:             {duration:.2f} seconds")
        print("│")
        print(f"│ Validation:           {"Success" if is_valid else "Failure"}\n")


# endregion
