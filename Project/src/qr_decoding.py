"""
A module that contains functions for decoding QR codes.
"""

from cv2.typing import MatLike
from pyzbar.pyzbar import ZBarSymbol, decode


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
