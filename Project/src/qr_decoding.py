"""
A module that contains functions for decoding QR codes.
"""

from functools import partial
from typing import List, Optional

from cv2 import QRCodeDetector
from pyzbar.pyzbar import ZBarSymbol, decode
from src.constants import TQDM_BAR_COLOUR_GREEN, TQDM_BAR_FORMAT, MatLike
from src.enums import QRDecodingLibrary
from src.performance import execute_parallel_tasks
from src.qr_configuration import QREncodingConfiguration
from tqdm import tqdm

DECODING_STRING = "Decoding QR code frames"


def decode_frames_to_data(
    frames: List[MatLike], configuration: Optional[QREncodingConfiguration]
) -> bytes:
    """
    Reads and decodes a QR code sequence video.

    Inspiration from:
    https://stackoverflow.com/questions/18954889/how-to-process-images-of-a-video-frame-by-frame-in-video-streaming-using-openc
    """

    if len(frames) == 0:
        raise ValueError("No frames were supplied to the decoding function.")

    decoded_frames = bytearray()

    if configuration is not None and configuration.enable_multiprocessing:
        results = execute_parallel_tasks(
            tasks=(partial(_decode_qr_image, frame, configuration) for frame in frames),
            length=len(frames),
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
            disable=not configuration.verbose if configuration is not None else True,
            bar_format=TQDM_BAR_FORMAT,
            colour=TQDM_BAR_COLOUR_GREEN,
        ):
            decoded_frames.extend(
                _decode_qr_image(
                    frames[i],
                    (configuration if configuration is not None else None),
                )
            )

    return bytes(decoded_frames)


def _decode_qr_image(image: MatLike, configuration: QREncodingConfiguration) -> bytes:
    """
    Decodes a QR code image and returns the resulting bytes data.

    If the image contains more than one QR code, all codes are decoded.
    """

    data = bytearray()

    if (
        configuration is None
        or configuration.qr_decoding_library == QRDecodingLibrary.PYZBAR
    ):
        decoded_list = decode(image, [ZBarSymbol.QRCODE])
        if not decoded_list:
            raise ValueError("Decoding did not yield any results.")

        for decoded_item in decoded_list:
            data.extend(decoded_item.data)

    elif configuration.qr_decoding_library == QRDecodingLibrary.OPEN_CV:
        detector = QRCodeDetector()

        text, _, _ = detector.detectAndDecode(image)
        if not text:
            raise ValueError("Decoding did not yield any results.")

        data = text.encode("utf-8")
    else:
        raise ValueError(
            f"Unexpected decoding library: {configuration.qr_decoding_library}"
        )

    try:
        return bytes(data)
    except Exception as e:
        raise ValueError(f"Could not convert decoded data to bytes: {e}")
