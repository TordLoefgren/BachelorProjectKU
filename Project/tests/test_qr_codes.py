import os
import unittest

from qrcode.image.base import BaseImage
from src.base import from_bytes, generate_random_string, to_bytes
from src.qr_codes import (
    QRVideoEncodingConfiguration,
    create_qr_video_encoding_pipeline,
    decode_qr_code_image,
    generate_qr_image,
)

TEST_VIDEO_FILENAME = "test_video.mp4"
STRING_DATA_LENGTH = 100


class TestQRCodes(unittest.TestCase):

    def setUp(self) -> None:
        self.qr_code_pipeline = create_qr_video_encoding_pipeline()

    def test__run_encode__should__create_video_file(self) -> None:
        # Arrange
        input_data = generate_random_string(STRING_DATA_LENGTH)

        # Act
        self.qr_code_pipeline.run_encode(input_data, TEST_VIDEO_FILENAME)

        # Assert
        self.assertTrue(os.path.exists(TEST_VIDEO_FILENAME))

    def test__run_decode__should__return_data_from_video_file(self) -> None:
        # Arrange
        input_data = generate_random_string(STRING_DATA_LENGTH)
        self.qr_code_pipeline.run_encode(input_data, TEST_VIDEO_FILENAME)
        # TODO: Mock the function, so we only need to call decode.

        # Act
        output_data = self.qr_code_pipeline.run_decode(TEST_VIDEO_FILENAME)

        # Assert
        self.assertTrue(os.path.exists(TEST_VIDEO_FILENAME))
        self.assertEqual(input_data, output_data)

    def test__run_pipeline__should__encode_video_and_return_data(self) -> None:
        # Arrange
        input_data = generate_random_string(STRING_DATA_LENGTH)

        # Act
        output_data = self.qr_code_pipeline.run_pipeline(
            input_data, TEST_VIDEO_FILENAME
        )

        # Assert
        self.assertTrue(os.path.exists(TEST_VIDEO_FILENAME))
        self.assertEqual(input_data, output_data)

    # --------------- Individual functions --------------------

    def test__generate_qr_code_image__should__return_qr_code_image(self) -> None:
        # Arrange
        input_data = generate_random_string(STRING_DATA_LENGTH)
        input_data_bytes = to_bytes(input_data)
        configuration = QRVideoEncodingConfiguration()

        # Act
        qr_code = generate_qr_image(input_data_bytes, configuration)

        # Assert
        self.assertIsInstance(qr_code, BaseImage)

    def test__decode_qr_code_image__should__return_original_data(self) -> None:
        # Arrange
        input_data = generate_random_string(STRING_DATA_LENGTH)
        input_data_bytes = to_bytes(input_data)
        configuration = QRVideoEncodingConfiguration()
        qr_code_image = generate_qr_image(input_data_bytes, configuration)

        # Act
        output_data_bytes = decode_qr_code_image(qr_code_image)
        output_data = from_bytes(output_data_bytes)

        # Assert
        self.assertEqual(input_data, output_data)

    def tearDown(self):
        # Remove test file after use.
        if os.path.exists(TEST_VIDEO_FILENAME):
            os.remove(TEST_VIDEO_FILENAME)
