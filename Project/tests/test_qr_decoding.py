import base64
from unittest import TestCase

from parameterized import parameterized
from src.enums import QREncodingLibrary
from src.qr_configuration import QREncodingConfiguration
from src.qr_decoding import _decode_qr_image
from src.qr_encoding import _generate_qr_image


class TestQRDecoding(TestCase):
    @parameterized.expand(
        [
            (b"Hello World", QREncodingLibrary.QRCODE),
            (b"\xff\xfe\xfd\xfa\x00\x01\xf0\xc1\xc0\x80", QREncodingLibrary.QRCODE),
            (
                b"\xc3\xa4\xc2\xbd\xc2\xa0\xc3\xa5\xc2\xa5\xc2\xbd",
                QREncodingLibrary.QRCODE,
            ),
            (
                b"TEST TEST!\xff\xfe\xfa\x00ABC\x00\x00\xff\xff",
                QREncodingLibrary.QRCODE,
            ),
            (b"Hello World", QREncodingLibrary.SEGNO),
            (b"\xff\xfe\xfd\xfa\x00\x01\xf0\xc1\xc0\x80", QREncodingLibrary.SEGNO),
            (
                b"\xc3\xa4\xc2\xbd\xc2\xa0\xc3\xa5\xc2\xa5\xc2\xbd",
                QREncodingLibrary.SEGNO,
            ),
            (b"TEST TEST!\xff\xfe\xfa\x00ABC\x00\x00\xff\xff", QREncodingLibrary.SEGNO),
        ]
    )
    def test__decode_qr_image__should__return_original_data(
        self,
        data: bytes,
        qr_encoding_library: QREncodingLibrary,
    ) -> None:
        # Arrange
        configuration = QREncodingConfiguration(qr_encoding_library=qr_encoding_library)

        data_b64 = base64.b64encode(data)
        qr_code_image = _generate_qr_image(data_b64, configuration)

        # Act
        result_b64 = _decode_qr_image(qr_code_image, configuration)
        result = base64.b64decode(result_b64)

        # Assert
        self.assertEqual(data, result)
        self.assertEqual(data_b64, result_b64)
