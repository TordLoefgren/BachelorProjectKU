"""
A module containing core classes and functions that are used by other modules in the package.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional, Union

from src.constants import T, TFrame, TSerialized
from src.utils import bytes_to_display


class PipelineValidationException(Exception):
    pass


@dataclass
class EncodingConfiguration:
    enable_parallelization: bool = True
    frames_per_second: int = 24
    show_decoding_window: bool = False
    verbose: bool = False
    chunk_size: Optional[int] = None
    max_workers: Optional[int] = None


SerializeFunction = Callable[[T], TSerialized]
DeserializeFunction = Callable[[TSerialized], T]

EncodeFunction = Callable[[Union[T, TSerialized], EncodingConfiguration], List[TFrame]]
DecodeFunction = Callable[[List[TFrame], EncodingConfiguration], Union[T, TSerialized]]

WriteVideoFunction = Callable[[List[TFrame], str, EncodingConfiguration], None]
ReadVideoFunction = Callable[[str, EncodingConfiguration], List[TFrame]]

ValidateFunction = Callable[[T, T], bool]


def validate_equal_sizes(input: T, output: T) -> bool:
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

    def run_encode(self, data: T, configuration: EncodingConfiguration) -> List[TFrame]:
        """
        Runs the encoding part of the pipeline.
        """

        if self.serialize_function is not None:
            data = self.serialize_function(data)

        if configuration.verbose:
            print(f"Encoding {bytes_to_display(len(data))}...")

        return self.encode_function(data, configuration)

    def run_encode_to_video(
        self, data: T, file_path: str, configuration: EncodingConfiguration
    ) -> None:
        """
        Runs the encoding part of the pipeline, including generating a video from frames.
        """

        frames = self.run_encode(data, configuration)

        self.write_video_function(frames, file_path, configuration)

    def run_decode(
        self,
        frames: List[TFrame],
        configuration: EncodingConfiguration,
    ) -> T:
        """
        Runs the decoding part of the pipeline.
        """

        if configuration.verbose:
            print("\nDecoding...")

        result = self.decode_function(frames, configuration)

        if self.deserialize_function is not None:
            result = self.deserialize_function(result)

        return result

    def run_decode_from_video(
        self, file_path: str, configuration: EncodingConfiguration
    ) -> None:
        """
        Runs the decoding part of the pipeline, including extracting frames from a video.
        """

        frames = self.read_video_function(file_path, configuration)

        return self.run_decode(frames, configuration)

    def run(
        self,
        data: T,
        file_path: str,
        configuration: EncodingConfiguration,
        mock: bool = False,
    ) -> T:
        """
        Runs the full pipeline, making a roundtrip.
        """

        verbose = configuration.verbose

        if verbose:
            print("└──── Running pipeline ────┐")
            print("                           │\n")

        frames_in = self.run_encode(data, configuration)

        if not mock:
            self.write_video_function(frames_in, file_path, configuration)
            frames_out = self.read_video_function(file_path, configuration)
        else:
            frames_out = frames_in

        result = self.run_decode(frames_out, configuration)

        if verbose:
            print("\n                           │")
            print("┌──── Finished pipeline ───┘\n")

        if self.validate_function is not None and not self.validate_function(
            data, result
        ):
            raise PipelineValidationException(
                "The decoded data does not match the encoded data. "
            )

        return result
