"""
A module that contains functions for encoding QR codes.
"""

import io
import math
from functools import partial
from typing import List, Tuple

import qrcode
import segno
from cv2.typing import MatLike
from PIL import Image
from qrcode.util import MODE_8BIT_BYTE, QRData
from src.enums import QRErrorCorrectionLevel, QRPackage
from src.performance import execute_parallel_tasks
from src.qr_configuration import QREncodingConfiguration
from src.video_processing import GridLayout, get_grid_layout, pil_to_cv2
from tqdm import tqdm

# TODO: The max size should be determined dynamically or through the configuration.
# We set a large max size in order to experiment with multi-QR code frames.
MAX_SIZE: Tuple[int, int] = (4000, 4000)


def generate_qr_images(
    data: bytes,
    configuration: QREncodingConfiguration,
) -> List[MatLike]:
    """
    Generates a list of QR code images based on chunks of the given data.
    """

    max_bytes = QRErrorCorrectionLevel.to_max_bytes(configuration.error_correction)
    if configuration.chunk_size is not None:
        max_bytes = min(configuration.chunk_size, max_bytes)

    if configuration.enable_parallelization:
        return execute_parallel_tasks(
            (
                partial(_generate_qr_image, data[i : i + max_bytes], configuration)
                for i in range(0, len(data), max_bytes)
            ),
            max_workers=configuration.max_workers,
            verbose=configuration.verbose,
            description="Generating QR code images",
        )
    else:
        images: List[MatLike] = []

        for i in tqdm(
            range(0, len(data), max_bytes),
            desc="Generating QR code images",
            disable=not configuration.verbose,
        ):
            image = _generate_qr_image(data[i : i + max_bytes], configuration)
            images.append(image)
        return images


def generate_image_frames(
    images: List[MatLike], configuration: QREncodingConfiguration
) -> List[MatLike]:
    """
    Generates a list of QR image frames, based on combined QR images.
    """

    if not images:
        return []

    # If the list contains a single image, or if every frame contains a single image each, we simply return the list.
    if configuration.qr_codes_per_frame == 1 or len(images) == 1:
        for i in tqdm(
            range(0, len(images)),
            desc="Generating QR code frames",
            disable=not configuration.verbose,
        ):
            pass
        return images

    # If more than one QR code is shown per frame, we need to generate a new combined image for every frame.
    total_frames = math.ceil(len(images) / configuration.qr_codes_per_frame)

    # TODO: Determine a way to minimize the image size, given the number and sizes of the frames.

    frames: List[MatLike] = []

    rectangles = [(image.shape[0], image.shape[1]) for image in images]

    # TODO: Implement parallelization option.
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


def _generate_qr_image(data: bytes, configuration: QREncodingConfiguration) -> MatLike:
    """
    Generates a QR code image based on the given data.

    Depending on the configuration, either 'qrcodes' or 'segno' will be used as a package.
    """

    max_bytes = QRErrorCorrectionLevel.to_max_bytes(configuration.error_correction)

    if len(data) > max_bytes:
        raise ValueError(
            f"Data size is {len(data)} bytes. The maximum allowed size for a QR code is {max_bytes} bytes."
        )

    image = None

    if configuration.qr_package == QRPackage.QRCODE:
        qr = qrcode.QRCode(
            border=configuration.border,
            box_size=configuration.box_size,
            error_correction=QRErrorCorrectionLevel.to_qrcode(
                configuration.error_correction
            ),
        )

        qr_data = QRData(data, mode=MODE_8BIT_BYTE)
        qr.add_data(qr_data)
        qr.make(fit=True)

        image = qr.make_image()

    elif configuration.qr_package == QRPackage.SEGNO:
        qr = segno.make_qr(
            content=data,
            mode="byte",
            error=QRErrorCorrectionLevel.to_segno(configuration.error_correction),
        )

        out = io.BytesIO()
        qr.save(out=out, scale=5, kind="png", border=10)
        out.seek(0)

        image = Image.open(out).convert("RGB")

    else:
        raise ValueError(f"Unexpected value: {type(configuration.qr_package)}.")

    return pil_to_cv2(image)


def _generate_image_frame(
    images: List[MatLike],
    layout: GridLayout,
) -> MatLike:
    """
    Generates a single QR image frame, based on combined QR images.
    """

    # TODO: Have this function use MatLike and not Image.

    frame = Image.new("RGB", layout.size)

    for i in range(len(images)):
        # We follow the indices set during the layout initialization.
        index = layout.rectangle_indices[i]
        current_image = images[index].get_image()
        Image.Image.paste(frame, current_image, layout.rectangles[index])

    return frame
