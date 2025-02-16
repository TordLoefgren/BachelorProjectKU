"""
A file that contains function for encoding, decoding, and creating QR codes in different formats.
"""

from typing import Any, List, Optional, Union

import cv2
import numpy as np
import qrcode
from qrcode.image.base import BaseImage


def generate_qr_code_image(
    data: str, box_size: int = 10, border: int = 4, fit: bool = True
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
    detector: Optional[cv2.QRCodeDetector] = None,
) -> str:
    """
    Decodes a QR code image.

    If the given image is a PIL image, it will first be converted to a CV2 image array.
    """

    if isinstance(image, BaseImage):
        image = _pil_to_cv2(image)

    if detector is None:
        detector = cv2.QRCodeDetector()

    return detector.detectAndDecode(image)[0]


def generate_qr_code_sequence_video(
    qr_code_images: List[BaseImage],
    output_filename: str,
    frames_per_second: int = 24,
) -> None:
    """
    Create a video from a list of QR code images.

    Inspiration from:
    https://www.tutorialspoint.com/opencv_python/opencv_python_video_images.htm
    """

    if not qr_code_images:
        return

    # Extract reference frame to determine the video image dimensions.
    reference_frame = _pil_to_cv2(qr_code_images[0])
    height, width = reference_frame.shape[:2]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(
        output_filename, fourcc, frames_per_second, (width, height)
    )

    for image in qr_code_images:
        frame = _pil_to_cv2(image)

        # Make sure that the frame is shaped correctly for the writer.
        # TODO: Consider extracting this to a function for when we have multiple QR codes per frame.
        if frame.shape[:2] != (height, width):
            frame = cv2.resize(frame, (width, height))

        video_writer.write(frame)

    video_writer.release()


def read_qr_code_sequence_video(
    input_filename: str, show_window: bool = False
) -> List[str]:
    """
    Reads and decodes a QR code sequence video.

    Inspiration from:
    https://stackoverflow.com/questions/18954889/how-to-process-images-of-a-video-frame-by-frame-in-video-streaming-using-openc
    """

    decoded_qr_code_data: List[Any] = []
    capture = cv2.VideoCapture(input_filename)
    code_detector = cv2.QRCodeDetector()

    while capture.isOpened():
        ret, frame = capture.read()
        if not ret:
            break

        if show_window:
            cv2.imshow(f"Reading '{input_filename}'", frame)

        # TODO: Consider implementing multidetect for several QR code reads per frame.
        # TODO: Consider only detecting the data and not decoding it here, making it more modular.
        decoded_info = decode_qr_code_image(frame, code_detector)
        decoded_qr_code_data.append(decoded_info)

        if show_window and cv2.waitKey(10) & 0xFF == ord("q"):
            break

    capture.release()

    if show_window:
        cv2.destroyAllWindows()

    return decoded_qr_code_data


def _pil_to_cv2(image: BaseImage) -> cv2.typing.MatLike:
    """
    Helper function that converts a PIL image to CV2 image array.

    PIL images are used by 'qrcode' behind the hood.

    We pre-convert the PIL image into RGB for safe conversion to CV2

    'qrcode' GitHub page:
    https://github.com/lincolnloop/python-qrcode
    """

    rgb_image = image.convert("RGB")
    image_array = np.array(rgb_image)
    cv2_image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

    return cv2_image_array


# region ------------ WIP and ideas section ------------


def generate_multi_qr_code_image(data: bytes, number_of_qr_codes: int) -> BaseImage:
    """
    Generates an image containing several QR codes based on the given data.
    """
    # TODO: Consider how best to divide the space between QR codes. This should be decided when looking at the data?
    pass


def generate_qr_code_images(data: bytes) -> List[BaseImage]:
    """
    Generates a sequence of QR code images based on the given data.
    """

    # TODO: Consider how to "chunk" the data. Different QR codes might have different restrictions.
    pass


def _determine_data_chunks(data: bytes):
    """
    Helper function that determines how many chunks the given data should be split into.
    """
    pass


# endregion
