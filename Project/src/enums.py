"""
A file containing enums that are used by other parts of the package.
"""

from enum import Enum, unique


@unique
class EncodingType(Enum):
    QR_CODE = 0
