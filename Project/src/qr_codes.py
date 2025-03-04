"""
A module that contains functions for encoding, decoding, and creating QR codes.
"""

import math
from dataclasses import dataclass
from functools import partial
from typing import Dict, List, Optional, Tuple

import qrcode
from cv2.typing import MatLike
from PIL import Image
from pyzbar.pyzbar import ZBarSymbol, decode
from qrcode.image.base import BaseImage
from src.base import (
    DeserializeFunction,
    ProcessingFunction,
    SerializeFunction,
    VideoEncodingConfiguration,
    VideoEncodingPipeline,
)
from src.enums import QRErrorCorrectLevels
from src.performance import execute_parallel_tasks, measure_task_performance
from src.utils import from_bytes, to_bytes
from src.video_processing import (
    GridLayout,
    create_frames_from_video,
    create_video_from_frames,
    get_grid_layout,
    pil_to_cv2,
)

# TODO: The max size should be determined dynamically or through the configuration.
# We set a max size in order to experiment with multi-QR code frames.
MAX_SIZE: Tuple[int, int] = (4000, 4000)

ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP: Dict[QRErrorCorrectLevels, int] = {
    QRErrorCorrectLevels.ERROR_CORRECT_L: 2953,
    QRErrorCorrectLevels.ERROR_CORRECT_M: 2331,
    QRErrorCorrectLevels.ERROR_CORRECT_Q: 1663,
    QRErrorCorrectLevels.ERROR_CORRECT_H: 1273,
}


@dataclass
class QRVideoEncodingConfiguration(VideoEncodingConfiguration):
    """
    A VideoEncodingConfiguration subclass that contains QR code specific metrics.
    """

    border: int = 4
    box_size: int = 10
    error_correction: QRErrorCorrectLevels = QRErrorCorrectLevels.ERROR_CORRECT_M
    qr_codes_per_frame: int = 1
    chunk_size: Optional[int] = None


def create_qr_video_encoding_pipeline(
    serialize_function: Optional[SerializeFunction] = to_bytes,
    deserialize_function: Optional[DeserializeFunction] = from_bytes,
    configuration: Optional[QRVideoEncodingConfiguration] = None,
    processing_function: Optional[ProcessingFunction] = None,
) -> VideoEncodingPipeline:
    """
    Creates an instance of the QR code video encoding pipeline.
    """

    if configuration is None:
        configuration = QRVideoEncodingConfiguration()

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
    )


def generate_qr_images(
    data: bytes,
    configuration: QRVideoEncodingConfiguration,
) -> List[MatLike]:
    """
    Generates a list of QR code images based on chunks of the given data.
    """

    images: List[BaseImage] = []

    max_bytes = ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP[configuration.error_correction]
    if configuration.chunk_size is not None:
        max_bytes = min(configuration.chunk_size, max_bytes)

    if configuration.enable_parallelization:
        return execute_parallel_tasks(
            [
                partial(_generate_qr_image, data[i : i + max_bytes], configuration)
                for i in range(0, len(data), max_bytes)
            ],
            configuration.max_workers,
        )
    else:
        for i in range(0, len(data), max_bytes):
            image = _generate_qr_image(data[i : i + max_bytes], configuration)
            images.append(image)

    return images


def generate_image_frames(
    images: List[BaseImage], configuration: QRVideoEncodingConfiguration
) -> List[MatLike]:
    """
    Generates a list of QR image frames, based on combined QR images.
    """

    if not images:
        return []

    # If the list contains a single image, or if every frame contains a single image each, we simply return the list.
    if configuration.qr_codes_per_frame == 1 or len(images) == 1:
        return [
            pil_to_cv2(image) if not isinstance(image, MatLike) else image
            for image in images
        ]

    # If more than one QR code is shown per frame, we need to generate a new combined image for every frame.
    total_frames = math.ceil(len(images) / configuration.qr_codes_per_frame)

    # TODO: Determine a way to minimize the image size, given the number and sizes of the frames.

    frames: List[MatLike] = []

    rectangles = [(image.pixel_size, image.pixel_size) for image in images]

    for i in range(total_frames):
        start = i * configuration.qr_codes_per_frame
        stop = (i + 1) * configuration.qr_codes_per_frame

        layout = get_grid_layout(
            MAX_SIZE,
            rectangles[start:stop],
        )

        new_frame = _generate_image_frame(
            images[start:stop],
            layout,
        )

        frames.append(new_frame)

    return frames


def encode_data_to_video(
    data: bytes, file_path: str, configuration: QRVideoEncodingConfiguration
) -> None:
    """
    Generates a sequence of QR code images from the given data and creates a video file with these images as frames.
    """

    images, duration = measure_task_performance(
        lambda: generate_qr_images(data, configuration)
    )
    print(f"Finished creating images in {duration:.4f} seconds.")

    frames, duration = measure_task_performance(
        lambda: generate_image_frames(images, configuration)
    )
    print(f"Finished creating frames in {duration:.4f} seconds.")

    duration = measure_task_performance(
        lambda: create_video_from_frames(
            frames, file_path, configuration.frames_per_second
        )
    )
    print(f"Finished creating video in {duration:.4f} seconds.\n")


def decode_video_to_data(
    file_path: str, configuration: QRVideoEncodingConfiguration
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
            [partial(_decode_qr_image, frame) for frame in frames],
            configuration.max_workers,
        )
        for result in results:
            decoded_frames.extend(result)
    else:
        for frame in frames:
            decoded_frames.extend(_decode_qr_image(frame))

    return bytes(decoded_frames)


def _generate_qr_image(
    data: bytes, configuration: QRVideoEncodingConfiguration
) -> BaseImage:
    """
    Generates a QR code image based on the given data.
    """

    max_bytes = ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP[configuration.error_correction]

    if len(data) > max_bytes:
        raise ValueError(
            f"Data size is {len(data)} bytes. The maximum allowed size for a QR code is {max_bytes} bytes."
        )

    qr = qrcode.QRCode(
        border=configuration.border,
        box_size=configuration.box_size,
        error_correction=configuration.error_correction,
    )

    qr.add_data(data)
    qr.make(fit=True)

    return pil_to_cv2(qr.make_image())


def _generate_image_frame(
    images: List[BaseImage],
    layout: GridLayout,
) -> MatLike:
    """
    Generates a single QR image frame, based on combined QR images.
    """

    frame = Image.new("RGB", layout.size)

    for i in range(len(images)):
        # We follow the indices set during the layout initialization.
        index = layout.rectangle_indices[i]
        current_image = images[index].get_image()
        Image.Image.paste(frame, current_image, layout.rectangles[index])

    return pil_to_cv2(frame)


def _decode_qr_image(
    image: MatLike,
) -> bytes:
    """
    Decodes a QR code image and returns the resulting bytes data.

    If the image contains more than one QR code, all codes are decoded.
    """

    decoded_list = decode(image, [ZBarSymbol.QRCODE])
    if not decoded_list:
        raise ValueError("The decoding did not yield any results.")

    data = bytearray()

    for decoded_item in decoded_list:
        data.extend(decoded_item.data)

    result = bytes(data)

    if not isinstance(result, bytes):
        raise ValueError(f"Unexpected value: {type(result)}. Expected bytes.")

    return result
