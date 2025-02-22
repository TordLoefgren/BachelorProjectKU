"""
A module that contains functions for encoding, decoding, and creating QR codes.
"""

from typing import List, Optional, Union

import cv2
import qrcode
from pyzbar.pyzbar import decode
from qrcode.image.base import BaseImage
from src.base import VideoEncodingConfiguration
from src.video_processing import (
    create_frames_from_video,
    create_video_from_frames,
    pil_to_cv2,
)


def generate_qr_code_image(
    data: bytes, box_size: int = 10, border: int = 4, fit: bool = True
) -> BaseImage:
    """
    Generates a QR code image based on the given data.

    The data is expected to be a base64 encoded string.
    """

    qr = qrcode.QRCode(box_size=box_size, border=border)

    # TODO: Consider adding exception handling for when the data size is too large for the QR code.
    qr.add_data(data)

    # TODO: If this function is used when creating multiple QR codes per frame, we might look into a custom fit or image factory.
    qr.make(fit=fit)

    return qr.make_image()


def decode_qr_code_image(
    image: Union[BaseImage, cv2.typing.MatLike],
) -> bytes:
    """
    Decodes a QR code image.

    If the given image is a PIL image, it will first be converted to a CV2 image array.
    """

    if isinstance(image, BaseImage):
        image = pil_to_cv2(image)

    decoded_list = decode(image)
    if not decoded_list:
        raise ValueError("Decoded list was empty.")

    data = decoded_list[0].data
    if not isinstance(data, bytes):
        raise ValueError(f"Unexpected value: {type(data)}. Expected bytes.")

    return data


def qr_encode_data(
    data: bytes,
    file_path: str,
    configuration: Optional[VideoEncodingConfiguration] = None,
) -> None:
    """
    Creates a sequence of QR codes from the given data and creates an encoded video.
    """

    # TODO: Implement config logic: i.e. customize video creation and reading.

    image = generate_qr_code_image(data)
    encode_qr_data_to_video([image], file_path)


def encode_qr_data_to_video(
    qr_code_images: List[BaseImage],
    file_path: str,
    frames_per_second: int = 24,
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
    create_video_from_frames(images, file_path, frames_per_second)


def decode_qr_video_to_data(file_path: str, show_window: bool = False) -> bytes:
    """
    Reads and decodes a QR code sequence video.

    Inspiration from:
    https://stackoverflow.com/questions/18954889/how-to-process-images-of-a-video-frame-by-frame-in-video-streaming-using-openc
    """

    frames = create_frames_from_video(file_path, show_window)

    decoded_frames = bytearray()
    for frame in frames:
        decoded_frames.extend(decode_qr_code_image(frame))

    return bytes(decoded_frames)


# region ------------ WIP and ideas section ------------

# endregion
