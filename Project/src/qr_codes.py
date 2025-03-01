"""
A module that contains functions for encoding, decoding, and creating QR codes.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import qrcode
from cv2.typing import MatLike
from PIL import Image
from pyzbar.pyzbar import decode
from qrcode.image.base import BaseImage
from src.base import (
    ProcessingFunction,
    VideoEncodingConfiguration,
    VideoEncodingPipeline,
)
from src.enums import QRErrorCorrectLevels
from src.utils import from_bytes, to_bytes
from src.video_processing import (
    GridLayout,
    create_frames_from_video,
    create_video_from_frames,
    get_grid_layout,
    pil_to_cv2,
)

MAX_WIDTH: int = 1920
MAX_HEIGHT: int = 1080
MAX_QR_SIZE: int = 177

MAX_SIZE: Tuple[int, int] = (MAX_WIDTH, MAX_HEIGHT)
MAX_QR_IMAGES_PER_FRAME: int = (MAX_WIDTH // MAX_QR_SIZE) * (MAX_HEIGHT // MAX_QR_SIZE)

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
        serialize_function=to_bytes,
        encoding_function=encode_data_to_video,
        decoding_function=decode_video_to_data,
        deserialize_function=from_bytes,
        configuration=configuration,
        processing_function=processing_function,
    )


def generate_qr_images(
    data: bytes,
    configuration: QRVideoEncodingConfiguration,
) -> List[BaseImage]:
    """
    Generates a list of QR code images based on chunks of the given data.
    """

    images: List[BaseImage] = []

    max_bytes = ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP[configuration.error_correction]
    if configuration.chunk_size is not None:
        max_bytes = min(max_bytes, configuration.chunk_size)

    for i in range(0, len(data), max_bytes):
        chunk = data[i : i + max_bytes]
        image = _generate_qr_image(chunk, configuration)
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
    image_length = len(images)
    if configuration.qr_codes_per_frame == 1 or len(images) == 1:
        return [pil_to_cv2(image) for image in images]

    # If more than one QR code is shown per frame, we need to generate a new combined image for every frame.
    combined_images_per_frame = image_length // configuration.qr_codes_per_frame
    if combined_images_per_frame > MAX_QR_IMAGES_PER_FRAME:
        raise NotImplementedError(
            "More than 60 QR images per frame has not been implemented."
        )

    total_frames = math.ceil(image_length / combined_images_per_frame)
    rectangles = [(image.width, image.width) for image in images]

    frames: List[MatLike] = []

    for i in range(total_frames):
        # TODO: Determine a way to minimize the image size, given the number and sizes of the frames.
        # TODO: Make sure that the border and box_size config fields are taken into account when calculating the layout.
        layout = get_grid_layout(
            MAX_SIZE, rectangles[i : i + combined_images_per_frame]
        )

        new_frame = _generate_image_frame(
            images[i : i + combined_images_per_frame], layout
        )

        frames.append(new_frame)

    return frames


def encode_data_to_video(
    data: bytes, file_path: str, configuration: QRVideoEncodingConfiguration
) -> None:
    """
    Creates a sequence of QR codes from the given data and creates an encoded video.
    """

    images = generate_qr_images(data, configuration)

    frames = generate_image_frames(images, configuration)

    create_video_from_frames(frames, file_path, configuration.frames_per_second)


def decode_video_to_data(
    file_path: str, configuration: QRVideoEncodingConfiguration
) -> bytes:
    """
    Reads and decodes a QR code sequence video.

    Inspiration from:
    https://stackoverflow.com/questions/18954889/how-to-process-images-of-a-video-frame-by-frame-in-video-streaming-using-openc
    """

    frames = create_frames_from_video(file_path, configuration.show_decoding_window)

    decoded_frames = bytearray()
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

    return qr.make_image()


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
    Decodes a QR code image.
    """

    decoded_list = decode(image)
    if not decoded_list:
        raise ValueError("The decoding did not yield a result.")

    data = decoded_list[0].data
    if not isinstance(data, bytes):
        raise ValueError(f"Unexpected value: {type(data)}. Expected bytes.")

    return data
