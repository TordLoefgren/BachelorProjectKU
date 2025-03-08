import base64
from unittest import TestCase

from src.enums import QRErrorCorrectionLevel
from src.qr_configuration import QREncodingConfiguration
from src.qr_decoding import _decode_qr_image
from src.qr_encoding import _generate_qr_image

ERROR_CORRECT_L = QRErrorCorrectionLevel.L
ERROR_CORRECT_M = QRErrorCorrectionLevel.M
ERROR_CORRECT_Q = QRErrorCorrectionLevel.Q
ERROR_CORRECT_H = QRErrorCorrectionLevel.H


class TestQRDecoding(TestCase):

    def test__decode_qr_image__should__return_original_data(self) -> None:
        # Arrange
        configuration = QREncodingConfiguration()
        input_data = b"\xc3\xa4\xc2\xbd\xc2\xa0\xc3\xa5\xc2\xa5\xc2\xbd"
        data = base64.b64encode(input_data)
        qr_code_image = _generate_qr_image(data, configuration)

        # Act
        output = _decode_qr_image(qr_code_image)
        output_data = base64.b64decode(output)
        # Assert
        self.assertEqual(data, output)
        self.assertEqual(input_data, output_data)
