"""
A file containing enums that are used by other parts of the package.
"""

from enum import Enum, IntEnum, unique


@unique
class EncodingType(Enum):
    QR_CODE = 0


@unique
class QRErrorCorrectLevels(IntEnum):
    """
    Can be mapped to the error correct levels in the 'qrcodes' package.
    """

    ERROR_CORRECT_L = 1
    ERROR_CORRECT_M = 0
    ERROR_CORRECT_Q = 3
    ERROR_CORRECT_H = 2
