"""
A module that contains the QR codes pipeline configuration.
"""

from dataclasses import dataclass

from src.base import EncodingConfiguration
from src.enums import QRDecodingLibrary, QREncodingLibrary, QRErrorCorrectionLevel


@dataclass
class QREncodingConfiguration(EncodingConfiguration):
    """
    A VideoEncodingConfiguration subclass that contains QR code specific metrics.
    """

    border: int = 40
    box_size: int = 10
    error_correction: QRErrorCorrectionLevel = QRErrorCorrectionLevel.M
    qr_codes_per_frame: int = 1
    qr_encoding_library: QREncodingLibrary = QREncodingLibrary.SEGNO
    qr_decoding_library: QRDecodingLibrary = QRDecodingLibrary.PYZBAR

    def __post_init__(self):
        if self.qr_codes_per_frame != 1:
            raise NotImplementedError()
