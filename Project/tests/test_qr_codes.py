import os
import unittest

from qrcode.image.base import BaseImage
from src.base import from_bytes, generate_bytes, generate_random_string, to_bytes
from src.enums import QRErrorCorrectLevels
from src.qr_codes import (
    BYTE_SIZE_LOOKUP,
    QRVideoEncodingConfiguration,
    create_qr_video_encoding_pipeline,
    decode_qr_image,
    generate_image_frame,
    generate_image_frames,
    generate_qr_image,
    generate_qr_images,
)

ERROR_CORRECT_LEVELS = [
    QRErrorCorrectLevels.ERROR_CORRECT_L,
    QRErrorCorrectLevels.ERROR_CORRECT_M,
    QRErrorCorrectLevels.ERROR_CORRECT_Q,
    QRErrorCorrectLevels.ERROR_CORRECT_H,
]
NUMBER_OF_CHUNKS = 4
STRING_DATA_LENGTH = 100
TEST_VIDEO_FILENAME = "test_video.mp4"


class TestQRCodes(unittest.TestCase):

    def setUp(self) -> None:
        self.qr_code_pipeline = create_qr_video_encoding_pipeline()

    # region ----- Pipeline -----

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

    # endregion

    # region ----- Individual functions -----

    def test__generate_qr_images__should__return_correct_number_of_images__when__data_is_chunked(
        self,
    ) -> None:

        for level in ERROR_CORRECT_LEVELS:
            # Arrange
            max_bytes = BYTE_SIZE_LOOKUP[level]

            input_data_bytes = generate_bytes(NUMBER_OF_CHUNKS * max_bytes)
            configuration = QRVideoEncodingConfiguration(error_correction=level)

            # Act
            images = generate_qr_images(input_data_bytes, configuration)

            # Assert
            self.assertEqual(len(images), NUMBER_OF_CHUNKS)

    def test__generate_qr_images__should__return_correct_number_of_images__when__data_is_chunked__and__data_has_remainder(
        self,
    ) -> None:

        for level in ERROR_CORRECT_LEVELS:
            # Arrange
            max_bytes = BYTE_SIZE_LOOKUP[level]

            input_data_bytes = generate_bytes(NUMBER_OF_CHUNKS * max_bytes + 1)
            configuration = QRVideoEncodingConfiguration(error_correction=level)

            # Act
            images = generate_qr_images(input_data_bytes, configuration)

            # Assert
            self.assertEqual(len(images), NUMBER_OF_CHUNKS + 1)

    def test__generate_image_frame__should__return_combined_images(self) -> None:
        for level in ERROR_CORRECT_LEVELS:
            # Arrange
            max_bytes = BYTE_SIZE_LOOKUP[level]
            size = (354, 354)

            input_data_bytes = generate_bytes(NUMBER_OF_CHUNKS * max_bytes)
            configuration = QRVideoEncodingConfiguration(
                error_correction=level, frames_per_second=2
            )
            images = generate_qr_images(input_data_bytes, configuration)

            # Act
            frame = generate_image_frame(images, size)

            # Assert
            self.assertEqual(len(images), NUMBER_OF_CHUNKS)
            self.assertEqual(frame.shape[:2], size)

    def test__generate_image_frames__should__return_combined_images(self) -> None:
        for level in ERROR_CORRECT_LEVELS:
            # Arrange
            max_bytes = BYTE_SIZE_LOOKUP[level]

            input_data_bytes = generate_bytes(NUMBER_OF_CHUNKS * max_bytes)
            configuration = QRVideoEncodingConfiguration(
                error_correction=level, frames_per_second=2
            )
            images = generate_qr_images(input_data_bytes, configuration)

            # Act
            frames = generate_image_frames(images, configuration)

            # Assert
            self.assertEqual(len(frames), NUMBER_OF_CHUNKS // 2)

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
        output_data_bytes = decode_qr_image(qr_code_image)
        output_data = from_bytes(output_data_bytes)

        # Assert
        self.assertEqual(input_data, output_data)

    # endregion

    def tearDown(self):
        # Remove test file after use.
        if os.path.exists(TEST_VIDEO_FILENAME):
            os.remove(TEST_VIDEO_FILENAME)
