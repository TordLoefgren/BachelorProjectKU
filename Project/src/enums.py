"""
A file containing enums that are used by other parts of the package.
"""

from enum import Enum, unique


@unique
class QRErrorCorrectionLevel(Enum):
    """
    Error correction level for QR codes.
    """

    L = 0
    M = 1
    Q = 2
    H = 3


@unique
class QRPackage(Enum):
    """
    QR code packages in use.
    """

    SEGNO = 0
    QRCODE = 1
