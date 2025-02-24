"""
A module that contains functions for encoding, decoding, and creating QR codes.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import qrcode
from cv2.typing import MatLike
from PIL import Image
from pyzbar.pyzbar import decode
from qrcode.image.base import BaseImage
from src.base import (
    ProcessingFunction,
    VideoEncodingConfiguration,
    VideoEncodingPipeline,
    from_bytes,
    to_bytes,
)
from src.enums import QRErrorCorrectLevels
from src.video_processing import (
    create_frames_from_video,
    create_video_from_frames,
    pil_to_cv2,
)

MAX_WIDTH = 1920
MAX_HEIGHT = 1080
MAX_SIZE: Tuple[int, int] = (MAX_WIDTH, MAX_HEIGHT)

MAX_QR_WIDTH = 177
MAX_QR_HEIGHT = 177
MAX_QR_SIZE: Tuple[int, int] = (MAX_QR_WIDTH, MAX_QR_HEIGHT)

MAX_QR_IMAGES_X = MAX_WIDTH // MAX_QR_WIDTH
MAX_QR_IMAGES_Y = MAX_HEIGHT // MAX_QR_HEIGHT
MAX_QR_IMAGES_PER_FRAME = MAX_QR_IMAGES_X * MAX_QR_IMAGES_Y

BYTE_SIZE_LOOKUP: Dict[QRErrorCorrectLevels, int] = {
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


def generate_qr_image(
    data: bytes, configuration: QRVideoEncodingConfiguration
) -> BaseImage:
    """
    Generates a QR code image based on the given data.
    """

    max_bytes = BYTE_SIZE_LOOKUP[configuration.error_correction]

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


def generate_qr_images(
    data: bytes, configuration: QRVideoEncodingConfiguration
) -> List[BaseImage]:
    """
    Generates a list of QR code images based on chunks of the given data.
    """

    images: List[BaseImage] = []

    max_bytes = BYTE_SIZE_LOOKUP[configuration.error_correction]

    for i in range(0, len(data), max_bytes):
        chunk = data[i : i + max_bytes]
        image = generate_qr_image(chunk, configuration)
        images.append(image)

    return images


def generate_image_frame(
    images: List[BaseImage],
    size: Tuple[int, int],
) -> MatLike:
    """
    Generates a QR image frame, based on combined QR images.
    """

    frame = Image.new("RGB", size)

    index = 0
    for x in range(0, size[0], MAX_QR_WIDTH):
        for y in range(0, size[1], MAX_QR_HEIGHT):
            current_image = images[index].get_image()
            Image.Image.paste(frame, current_image, (x, y))

            if index >= len(images):
                break

            index += 1

    return pil_to_cv2(frame)


def decode_qr_image(
    image: Union[BaseImage, MatLike],
) -> bytes:
    """
    Decodes a QR code image.

    If the given image is a PIL image, it will first be converted to a CV2 image array.
    """

    if isinstance(image, BaseImage):
        image = pil_to_cv2(image)

    decoded_list = decode(image)
    if not decoded_list:
        raise ValueError("The decoding did not yield a result.")

    data = decoded_list[0].data
    if not isinstance(data, bytes):
        raise ValueError(f"Unexpected value: {type(data)}. Expected bytes.")

    return data


def qr_encode_data(
    data: bytes, file_path: str, configuration: QRVideoEncodingConfiguration
) -> None:
    """
    Creates a sequence of QR codes from the given data and creates an encoded video.
    """

    images = generate_qr_images(data, configuration)
    # frames = generate_image_frames(images, configuration)
    encode_qr_data_to_video(images, file_path, configuration)


def encode_qr_data_to_video(
    qr_code_images: List[BaseImage],
    file_path: str,
    configuration: QRVideoEncodingConfiguration,
) -> None:
    """
    Create a video from a list of QR code images.

    Inspiration from:
    https://www.tutorialspoint.com/opencv_python/opencv_python_video_images.htm
    """

    if not qr_code_images:
        return

    # Convert images to image arrays.
    images = [pil_to_cv2(image) for image in qr_code_images]

    # Generate video from images.
    create_video_from_frames(images, file_path, configuration.frames_per_second)


def decode_qr_video_to_data(
    file_path: str, configuration: QRVideoEncodingConfiguration
) -> bytes:
    """
    Reads and decodes a QR code sequence video.

    Inspiration from:
    https://stackoverflow.com/questions/18954889/how-to-process-images-of-a-video-frame-by-frame-in-video-streaming-using-openc
    """

    frames = create_frames_from_video(file_path, configuration.show_window)

    decoded_frames = bytearray()
    for frame in frames:
        decoded_frames.extend(decode_qr_image(frame))

    return bytes(decoded_frames)


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

    return VideoEncodingPipeline(
        serialize_function=to_bytes,
        encoding_function=qr_encode_data,
        decoding_function=decode_qr_video_to_data,
        deserialize_function=from_bytes,
        configuration=configuration,
        processing_function=processing_function,
    )


# region ------------ WIP and ideas section ------------


def generate_image_frames(
    images: List[BaseImage], configuration: QRVideoEncodingConfiguration
) -> List[MatLike]:
    """
    Generates a list of QR image frames, based on combined QR images.
    """

    frames = []

    if configuration.frames_per_second == 1:
        return images

    # We determine how many images needs to be combined.

    # We now try to fill out as many full size images as we can.
    # TODO: Include option to set resolution (maybe a minimum of the size of the largest QR code).

    number_of_combined_images = len(images) // configuration.frames_per_second
    if number_of_combined_images > MAX_QR_IMAGES_PER_FRAME:
        raise NotImplementedError()

    # TODO: Determine how to divide the images. Maybe even include a division strategy: fill or space out.
    # generate_image_frame()

    return frames


# endregion
