"""
A module that contains dataclasses relating to QR codes pipeline.
"""

from functools import partial
from typing import List, Optional

from cv2.typing import MatLike
from src.base import (
    DeserializeFunction,
    ProcessingFunction,
    SerializeFunction,
    ValidationFunction,
    VideoEncodingPipeline,
)
from src.performance import execute_parallel_tasks, measure_task_performance
from src.qr_configuration import QREncodingConfiguration
from src.qr_decoding import _decode_qr_image
from src.qr_encoding import generate_image_frames, generate_qr_images
from src.video_processing import create_frames_from_video, create_video_from_frames


def encode_data_to_video(
    data: bytes, file_path: str, configuration: QREncodingConfiguration
) -> None:
    """
    Generates a sequence of QR code images from the given data and creates a video file with these images as frames.
    """

    images = generate_qr_images(data, configuration)

    frames = generate_image_frames(images, configuration)

    duration = measure_task_performance(
        partial(
            create_video_from_frames, frames, file_path, configuration.frames_per_second
        )
    )
    if configuration.verbose:
        print(f"Finished creating video in {duration:.4f} seconds.")


def decode_video_to_data(
    file_path: str, configuration: QREncodingConfiguration
) -> bytes:
    """
    Reads and decodes a QR code sequence video.

    Inspiration from:
    https://stackoverflow.com/questions/18954889/how-to-process-images-of-a-video-frame-by-frame-in-video-streaming-using-openc
    """

    frames: List[MatLike] = create_frames_from_video(
        file_path, configuration.show_decoding_window
    )

    decoded_frames = bytearray()

    if configuration.enable_parallelization:
        results = execute_parallel_tasks(
            tasks=(partial(_decode_qr_image, frame) for frame in frames),
            max_workers=configuration.max_workers,
            verbose=configuration.verbose,
            description="Decoding QR code frames",
        )
        for result in results:
            decoded_frames.extend(result)
    else:
        for frame in frames:
            decoded_frames.extend(_decode_qr_image(frame))

    return bytes(decoded_frames)


def create_qr_video_encoding_pipeline(
    serialize_function: Optional[SerializeFunction] = None,
    deserialize_function: Optional[DeserializeFunction] = None,
    configuration: Optional[QREncodingConfiguration] = None,
    processing_function: Optional[ProcessingFunction] = None,
    validation_function: Optional[ValidationFunction] = None,
) -> VideoEncodingPipeline:
    """
    Creates an instance of the QR code video encoding pipeline.
    """

    if configuration is None:
        configuration = QREncodingConfiguration()

    # TODO: Add processing function.
    if processing_function is not None:
        raise NotImplementedError("Processing function is not implemented.")

    return VideoEncodingPipeline(
        encoding_function=encode_data_to_video,
        decoding_function=decode_video_to_data,
        configuration=configuration,
        serialize_function=serialize_function,
        deserialize_function=deserialize_function,
        processing_function=processing_function,
        validation_function=validation_function,
    )
