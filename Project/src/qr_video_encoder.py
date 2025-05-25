from typing import List

from src.base import Base64Serializer, Result, Serializer
from src.qr_configuration import QREncodingConfiguration
from src.qr_pipeline import create_qr_video_encoding_pipeline


class QRVideoEncoder[TFrame]:
    """A class that encapsulates the logic necessary to encode data to QR code videos."""

    def __init__(
        self,
        configuration: QREncodingConfiguration,
        serializer: Serializer = Base64Serializer,
    ) -> None:
        self.configuration = configuration
        self.pipeline = create_qr_video_encoding_pipeline(serializer=serializer)

    def encode(self, data: bytes, file_path: str) -> List[TFrame]:
        return self.pipeline.encode(data, self.configuration, file_path)

    def decode(self, file_path: str) -> bytes:
        return self.pipeline.decode(self.configuration, file_path)

    def roundtrip(self, data: bytes, file_path: str) -> Result[bytes]:
        return self.pipeline.run(data, file_path, self.configuration)
