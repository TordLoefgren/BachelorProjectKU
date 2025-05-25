from unittest import TestCase

from parameterized import parameterized
from src.enums import QRErrorCorrectionLevel
from src.qr_configuration import QREncodingConfiguration
from src.qr_encoding import generate_qr_frames
from src.utils import generate_random_bytes


class TestQREncoding(TestCase):
    """
    Inspiration from:
    https://medium.com/@samarthgvasist/parameterized-unit-testing-in-python-9be82fa7e17f
    """

    @parameterized.expand(
        [
            (QRErrorCorrectionLevel.L, 0, 4, 4),
            (QRErrorCorrectionLevel.M, 0, 4, 4),
            (QRErrorCorrectionLevel.Q, 0, 4, 4),
            (QRErrorCorrectionLevel.H, 0, 4, 4),
            (QRErrorCorrectionLevel.L, 1, 4, 5),
            (QRErrorCorrectionLevel.M, 1, 4, 5),
            (QRErrorCorrectionLevel.Q, 1, 4, 5),
            (QRErrorCorrectionLevel.H, 1, 4, 5),
        ],
    )
    def test__generate_qr_frames__should__return_correct_number_of_frames__when__data_is_chunked(
        self, error_correct_level, remainder, chunk_size, expected_frames_length
    ) -> None:

        # Arrange
        max_bytes = QRErrorCorrectionLevel.to_max_bytes(error_correct_level)

        input_data_bytes = generate_random_bytes(chunk_size * max_bytes + remainder)
        configuration = QREncodingConfiguration(error_correction=error_correct_level)

        # Act
        frames = generate_qr_frames(input_data_bytes, configuration)

        # Assert
        self.assertEqual(len(frames), expected_frames_length)
