import base64
from unittest import TestCase

from parameterized import parameterized
from src.qr_configuration import QREncodingConfiguration
from src.qr_decoding import _decode_qr_image
from src.qr_encoding import _generate_qr_image


class TestQRDecoding(TestCase):

    @parameterized.expand(
        [
            (b"\xc3\xa4\xc2\xbd\xc2\xa0\xc3\xa5\xc2\xa5\xc2\xbd"),
            (b"0xff, 0xfe, 0xfd, 0xfa, 0x00, 0x01, 0xf0, 0xc1, 0xc0, 0x80"),
            (b"0xff, 0xfe, 0xfd, 0xfa, 0x00, 0x01, 0xf0, 0xc1, 0xc0, 0x80"),
            (b"0xff, 0xfe, 0xfd, 0xfc, 0xfb, 0xfa, 0xf9, 0xf8, 0xf7, 0xf6"),
            (b"0x00, 0x00, 0x01, 0x02, 0x00, 0x00, 0xff, 0x00, 0xab, 0xcd, 0xef"),
            (b"0xed, 0xa0, 0x80, 0xed, 0xbf, 0xbf"),
            (b"Quack quack!\xff\xfe\xfa\x00\x10ABC\x00\x00\xff\xff"),
            (b"0xFE"),
            (b"0xFF"),
            (b"0x80"),
            (b"0xED, 0xA0, 0x80"),
        ],
    )
    def test__decode_qr_image__should__return_original_data(self, data) -> None:
        # Arrange
        configuration = QREncodingConfiguration()
        data_b64 = base64.b64encode(data)
        qr_code_image = _generate_qr_image(data_b64, configuration)

        # Act
        result_b64 = _decode_qr_image(qr_code_image)
        result = base64.b64decode(result_b64)

        # Assert
        self.assertEqual(data, result)
        self.assertEqual(data_b64, result_b64)
