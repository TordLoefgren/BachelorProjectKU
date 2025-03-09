"""
A module that contains functions for decoding QR codes.
"""

from functools import partial
from typing import List

from cv2.typing import MatLike
from pyzbar.pyzbar import ZBarSymbol, decode
from src.constants import TQDM_BAR_COLOUR_GREEN, TQDM_BAR_FORMAT_STRING
from src.performance import execute_parallel_tasks
from src.qr_configuration import QREncodingConfiguration
from tqdm import tqdm

DECODING_STRING = "Decoding QR code frames"


def decode_frames_to_data(
    frames: List[MatLike], configuration: QREncodingConfiguration
) -> bytes:
    """
    Reads and decodes a QR code sequence video.

    Inspiration from:
    https://stackoverflow.com/questions/18954889/how-to-process-images-of-a-video-frame-by-frame-in-video-streaming-using-openc
    """

    decoded_frames = bytearray()

    if configuration.enable_parallelization:
        results = execute_parallel_tasks(
            tasks=(partial(_decode_qr_image, frame) for frame in frames),
            max_workers=configuration.max_workers,
            verbose=configuration.verbose,
            description=DECODING_STRING,
        )
        for result in results:
            decoded_frames.extend(result)
    else:
        for i in tqdm(
            range(0, len(frames)),
            desc=DECODING_STRING,
            disable=not configuration.verbose,
            bar_format=TQDM_BAR_FORMAT_STRING,
            colour=TQDM_BAR_COLOUR_GREEN,
        ):
            decoded_frames.extend(_decode_qr_image(frames[i]))

    return bytes(decoded_frames)


def _decode_qr_image(
    image: MatLike,
) -> bytes:
    """
    Decodes a QR code image and returns the resulting bytes data.

    If the image contains more than one QR code, all codes are decoded.
    """

    decoded_list = decode(image, [ZBarSymbol.QRCODE])
    if not decoded_list:
        raise ValueError("Decoding did not yield any results.")

    data = bytearray()

    for decoded_item in decoded_list:
        data.extend(decoded_item.data)

    try:
        result = bytes(data)
    except Exception:
        raise ValueError(f"Unexpected value: {type(result)}. Expected bytes.")

    return result
