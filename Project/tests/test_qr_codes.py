import os
from unittest import TestCase

from src.enums import QRErrorCorrectLevels
from src.qr_codes import (
    ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP,
    QRVideoEncodingConfiguration,
    _decode_qr_image,
    _generate_qr_image,
    create_qr_video_encoding_pipeline,
    generate_image_frames,
    generate_qr_images,
)
from src.utils import (
    from_bytes,
    generate_random_bytes,
    generate_random_string,
    remove_file,
    to_bytes,
)
from src.video_processing import pil_to_cv2

ERROR_CORRECT_L = QRErrorCorrectLevels.ERROR_CORRECT_L
ERROR_CORRECT_M = QRErrorCorrectLevels.ERROR_CORRECT_M
ERROR_CORRECT_Q = QRErrorCorrectLevels.ERROR_CORRECT_Q
ERROR_CORRECT_H = QRErrorCorrectLevels.ERROR_CORRECT_H

STRING_DATA_LENGTH = 100
TEST_VIDEO_FILENAME = "test_video.mp4"


class TestQRCodesPipeline(TestCase):

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

    def tearDown(self):
        # Remove test file after use.
        remove_file(TEST_VIDEO_FILENAME)


class TestQRCodesEncoding(TestCase):

    def test__generate_qr_images__should__return_correct_number_of_images__when__data_is_chunked(
        self,
    ) -> None:

        test_cases = [
            (ERROR_CORRECT_L, 0, 4, 4),
            (ERROR_CORRECT_M, 0, 4, 4),
            (ERROR_CORRECT_Q, 0, 4, 4),
            (ERROR_CORRECT_H, 0, 4, 4),
            (ERROR_CORRECT_L, 1, 4, 5),
            (ERROR_CORRECT_M, 1, 4, 5),
            (ERROR_CORRECT_Q, 1, 4, 5),
            (ERROR_CORRECT_H, 1, 4, 5),
        ]

        for (
            error_correct_level,
            remainder,
            chunk_size,
            expected_images_length,
        ) in test_cases:
            with self.subTest(
                error_correct_level=error_correct_level,
                remainder=remainder,
                chunk_size=chunk_size,
                expected_images_length=expected_images_length,
            ):
                # Arrange
                max_bytes = ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP[error_correct_level]

                input_data_bytes = generate_random_bytes(
                    chunk_size * max_bytes + remainder
                )
                configuration = QRVideoEncodingConfiguration(
                    error_correction=error_correct_level
                )

                # Act
                images = generate_qr_images(input_data_bytes, configuration)

                # Assert
                self.assertEqual(len(images), expected_images_length)

    def test__generate_image_frames__should__return_combined_images(self) -> None:
        test_cases = [
            (ERROR_CORRECT_L, 2, 4, 2),
            (ERROR_CORRECT_M, 2, 4, 2),
            (ERROR_CORRECT_Q, 2, 4, 2),
            (ERROR_CORRECT_H, 2, 4, 2),
        ]

        for (
            error_correct_level,
            qr_codes_per_frame,
            chunk_size,
            expected_frames_length,
        ) in test_cases:
            with self.subTest(
                error_correct_level=error_correct_level,
                qr_codes_per_frame=qr_codes_per_frame,
                chunk_size=chunk_size,
                expected_frames_length=expected_frames_length,
            ):

                # Arrange
                max_bytes = ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP[error_correct_level]

                input_data_bytes = generate_random_bytes(chunk_size * max_bytes)
                configuration = QRVideoEncodingConfiguration(
                    error_correction=error_correct_level,
                    qr_codes_per_frame=qr_codes_per_frame,
                )
                images = generate_qr_images(input_data_bytes, configuration)

                # Act
                frames = generate_image_frames(images, configuration)

                # Assert
                self.assertEqual(len(frames), expected_frames_length)


class TestQRCodesDecoding(TestCase):

    def test__decode_qr_code_image__should__return_original_data(self) -> None:
        # Arrange
        input_data = generate_random_string(STRING_DATA_LENGTH)
        input_data_bytes = to_bytes(input_data)
        configuration = QRVideoEncodingConfiguration()
        qr_code_image = _generate_qr_image(input_data_bytes, configuration)
        qr_code_image_frame = pil_to_cv2(qr_code_image)

        # Act
        output_data_bytes = _decode_qr_image(qr_code_image_frame)
        output_data = from_bytes(output_data_bytes)

        # Assert
        self.assertEqual(input_data, output_data)

    def test__decode_qr_code_image__should__return_original_data__when_image_contains_multiple(
        self,
    ) -> None:
        # Arrange

        max_bytes = ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP[ERROR_CORRECT_M]
        input_data = generate_random_string(max_bytes * 2)
        input_data_bytes = to_bytes(input_data)
        configuration = QRVideoEncodingConfiguration(
            qr_codes_per_frame=2, error_correction=ERROR_CORRECT_M
        )
        qr_code_images = generate_qr_images(input_data_bytes, configuration)
        qr_code_image_frames = generate_image_frames(qr_code_images, configuration)

        # Act
        output_data_bytes = _decode_qr_image(qr_code_image_frames[0])
        output_data = from_bytes(output_data_bytes)

        # Assert
        self.assertEqual(len(input_data), len(output_data))
        self.assertCountEqual(input_data, output_data)
