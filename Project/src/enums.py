"""
A file containing enums that are used by other parts of the package.
"""

from enum import Enum, unique
from typing import Dict


@unique
class QRErrorCorrectionLevel(Enum):
    """
    Error correction level for QR codes.
    """

    L = 0
    M = 1
    Q = 2
    H = 3

    @staticmethod
    def to_segno(error: "QRErrorCorrectionLevel") -> str:
        """
        Returns the 'segno' error correction level equivalent.
        """

        if not isinstance(error, QRErrorCorrectionLevel):
            raise ValueError(f"Unexpected value: {type(error)}.")

        error_to_segno_lookup: Dict[QRErrorCorrectionLevel, str] = {
            QRErrorCorrectionLevel.L: "L",
            QRErrorCorrectionLevel.M: "M",
            QRErrorCorrectionLevel.Q: "Q",
            QRErrorCorrectionLevel.H: "H",
        }

        return error_to_segno_lookup[error]

    @staticmethod
    def to_qrcode(error: "QRErrorCorrectionLevel") -> int:
        """
        Returns the 'qrcodes' error correction level equivalent.
        """

        if not isinstance(error, QRErrorCorrectionLevel):
            raise ValueError(f"Unexpected value: {type(error)}.")

        error_to_qrcodes_lookup: Dict[QRErrorCorrectionLevel, int] = {
            QRErrorCorrectionLevel.L: 1,
            QRErrorCorrectionLevel.M: 0,
            QRErrorCorrectionLevel.Q: 3,
            QRErrorCorrectionLevel.H: 2,
        }

        return error_to_qrcodes_lookup[error]

    @staticmethod
    def to_max_bytes(error: "QRErrorCorrectionLevel") -> int:
        """
        Returns the maximum bytes size for the given error correction level.

        See: https://www.qrcode.com/en/about/version.html

        """

        if not isinstance(error, QRErrorCorrectionLevel):
            raise ValueError(f"Unexpected value: {type(error)}.")

        error_to_max_bytes_lookup: Dict[QRErrorCorrectionLevel, int] = {
            QRErrorCorrectionLevel.L: 2953,
            QRErrorCorrectionLevel.M: 2331,
            QRErrorCorrectionLevel.Q: 1663,
            QRErrorCorrectionLevel.H: 1273,
        }

        return error_to_max_bytes_lookup[error]


@unique
class QRPackage(Enum):
    """
    QR code packages in use.
    """

    SEGNO = 0
    QRCODE = 1
