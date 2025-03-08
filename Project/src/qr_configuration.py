"""
A module that contains the QR codes pipeline configuration.
"""

from dataclasses import dataclass

from src.base import EncodingConfiguration
from src.enums import QRErrorCorrectionLevel, QRPackage


@dataclass
class QREncodingConfiguration(EncodingConfiguration):
    """
    A VideoEncodingConfiguration subclass that contains QR code specific metrics.
    """

    border: int = 4
    box_size: int = 10
    error_correction: QRErrorCorrectionLevel = QRErrorCorrectionLevel.M
    qr_codes_per_frame: int = 1
    qr_package: QRPackage = QRPackage.SEGNO
