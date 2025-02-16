import os
import unittest

from qrcode.image.base import BaseImage
from src.base import from_base64, generate_random_string, to_base64
from src.qr_codes import (
    decode_qr_code_image,
    generate_qr_code_image,
    generate_qr_code_sequence_video,
    read_qr_code_sequence_video,
)

TEST_VIDEO_FILENAME = "TEST_VIDEO.mp4"
INPUT_DATA_LENGTHS = [0, 5, 10, 50, 100, 150, 200, 250]
STRING_DATA_LENGTH = 30


class TestQRCodes(unittest.TestCase):

    def test__generate_qr_code_image__should__return_qr_code_image(self) -> None:
        # Arrange
        input_data = generate_random_string(STRING_DATA_LENGTH)
        input_base_64_string = to_base64(input_data)

        # Act
        qr_code = generate_qr_code_image(input_base_64_string)

        # Assert
        self.assertIsInstance(qr_code, BaseImage)

    def test__decode_qr_code_image__should__return_original_data(self) -> None:
        # Arrange
        input_data = generate_random_string(STRING_DATA_LENGTH)
        input_base_64_string = to_base64(input_data)
        qr_code_image = generate_qr_code_image(input_base_64_string)

        # Act
        output_base_64_string = decode_qr_code_image(qr_code_image)
        output_data = from_base64(output_base_64_string, is_string=True)

        # Assert
        self.assertEqual(input_data, output_data)

    def test__generate_qr_code_sequence_video__should__(
        self,
    ) -> None:
        # TODO: Add test case.
        self.fail("Not implemented.")

    def test__read_qr_code_sequence_video__should__(
        self,
    ) -> None:
        # TODO: Add test case.
        self.fail("Not implemented.")

    def test__round_trip__should__successfully_encode_and_decode_video(self) -> None:
        # TODO: This test is failing. Fix failing test by solving the decoding issue in 'read_qr_code_sequence_video'.

        for i, data_length in enumerate(INPUT_DATA_LENGTHS):
            # Arrange
            input_data = [
                generate_random_string(STRING_DATA_LENGTH) for _ in range(data_length)
            ]
            base_64_input_data = [to_base64(data) for data in input_data]

            # Act
            qr_codes = [generate_qr_code_image(data) for data in base_64_input_data]

            enumerated_video_filename = f" - {i + 1}.".join(
                TEST_VIDEO_FILENAME.split(".")
            )
            generate_qr_code_sequence_video(qr_codes, enumerated_video_filename)

            base_64_output_data = read_qr_code_sequence_video(enumerated_video_filename)
            output_data = [
                from_base64(data, is_string=True) for data in base_64_output_data
            ]

            # Remove test file after use.
            if os.path.exists(enumerated_video_filename):
                os.remove(enumerated_video_filename)

            # Assert
            self.assertCountEqual(input_data, output_data)
            self.assertEqual(input_data, output_data)
