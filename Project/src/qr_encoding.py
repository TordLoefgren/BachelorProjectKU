"""
A module that contains functions for encoding QR codes.
"""

import io
from functools import partial
from typing import Iterator, Optional

import qrcode
import segno
from PIL import Image
from qrcode.util import MODE_8BIT_BYTE, QRData
from src.constants import RGB, TQDM_BAR_COLOUR_GREEN, TQDM_BAR_FORMAT, MatLike
from src.enums import QREncodingLibrary, QRErrorCorrectionLevel
from src.performance import execute_parallel_iter_tasks
from src.qr_configuration import QREncodingConfiguration
from src.utils import bytes_to_display
from src.video_processing import _pil_to_cv2
from tqdm import tqdm

ENCODING_QR_FRAMES_STRING = "Encoding QR code frames"


def encode_data_to_frames(
    data: bytes,
    configuration: Optional[QREncodingConfiguration],
    is_header: bool = False,
) -> Iterator[MatLike]:
    """
    Generates a sequence of QR code images from the given data and creates frames from these images.
    """

    return generate_qr_frames(data, configuration, is_header)


def qr_version_for_size(data_len: int, error_correction: QRErrorCorrectionLevel) -> int:
    """
    Returns the smallest possible QR version that can hold payload.
    """

    data = b"\0" * data_len

    qr = segno.make_qr(
        content=data,
        mode="byte",
        error=QRErrorCorrectionLevel.to_segno(error_correction),
    )

    return qr.version


def generate_qr_frames(
    data: bytes,
    configuration: Optional[QREncodingConfiguration],
    is_header: bool = False,
) -> Iterator[MatLike]:
    """
    Generates a list of QR code images based on chunks of the given data.
    """

    max_bytes = QRErrorCorrectionLevel.to_max_bytes(configuration.error_correction)

    if is_header:
        yield _generate_qr_image(data, configuration)
        return

    if configuration.chunk_size is not None:
        max_bytes = min(configuration.chunk_size, max_bytes)

    chunks = (data[i : i + max_bytes] for i in range(0, len(data), max_bytes))

    if configuration.enable_multiprocessing:
        yield from execute_parallel_iter_tasks(
            (partial(_generate_qr_image, chunk, configuration) for chunk in chunks),
            length=len(range(0, len(data), max_bytes)),
            max_workers=configuration.max_workers,
            verbose=configuration.verbose,
            description=ENCODING_QR_FRAMES_STRING,
        )
    else:
        for chunk in tqdm(
            chunks,
            desc=ENCODING_QR_FRAMES_STRING,
            disable=not configuration.verbose,
            bar_format=TQDM_BAR_FORMAT,
            colour=TQDM_BAR_COLOUR_GREEN,
        ):
            yield _generate_qr_image(chunk, configuration)


def _generate_qr_image(data: bytes, configuration: QREncodingConfiguration) -> MatLike:
    """
    Generates a QR code image based on the given data.

    Depending on the configuration, either 'qrcodes' or 'segno' will be used as a package.
    """

    max_bytes = QRErrorCorrectionLevel.to_max_bytes(configuration.error_correction)

    if len(data) > max_bytes:
        raise ValueError(
            f"Data size is {bytes_to_display(len(data))}. The maximum allowed size for a QR code is {bytes_to_display(max_bytes)}."
        )

    image = None

    if configuration.qr_encoding_library == QREncodingLibrary.QRCODE:
        qr = qrcode.QRCode(
            border=configuration.border,
            box_size=configuration.box_size,
            error_correction=QRErrorCorrectionLevel.to_qrcode(
                configuration.error_correction
            ),
        )

        qr.add_data(QRData(data, mode=MODE_8BIT_BYTE))
        qr.make(fit=True)

        image = qr.make_image()

    elif configuration.qr_encoding_library == QREncodingLibrary.SEGNO:
        qr = segno.make_qr(
            content=data,
            mode="byte",
            error=QRErrorCorrectionLevel.to_segno(configuration.error_correction),
        )

        out = io.BytesIO()
        qr.save(out=out, scale=5, kind="png", border=configuration.border)
        out.seek(0)

        image = Image.open(out).convert(RGB)

    else:
        raise ValueError(
            f"Unexpected value: {type(configuration.qr_encoding_library)}."
        )

    return _pil_to_cv2(image)
