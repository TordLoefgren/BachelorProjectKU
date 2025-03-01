import os
from unittest import TestCase

from qrcode.image.base import BaseImage
from src.enums import QRErrorCorrectLevels
from src.qr_codes import (
    ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP,
    QRVideoEncodingConfiguration,
    create_qr_video_encoding_pipeline,
    decode_qr_image,
    generate_image_frame,
    generate_image_frames,
    generate_qr_image,
    generate_qr_images,
)
from src.utils import (
    from_bytes,
    generate_random_bytes,
    generate_random_string,
    remove_file,
    to_bytes,
)
from src.video_processing import GridLayout, pil_to_cv2

ERROR_CORRECT_LEVELS = [
    QRErrorCorrectLevels.ERROR_CORRECT_L,
    QRErrorCorrectLevels.ERROR_CORRECT_M,
    QRErrorCorrectLevels.ERROR_CORRECT_Q,
    QRErrorCorrectLevels.ERROR_CORRECT_H,
]
NUMBER_OF_CHUNKS = 4
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

    def tearDown(self):
        # Remove test file after use.
        remove_file(TEST_VIDEO_FILENAME)


class TestQRCodesFunctions(TestCase):

    def test__generate_qr_images__should__return_correct_number_of_images__when__data_is_chunked(
        self,
    ) -> None:

        for level in ERROR_CORRECT_LEVELS:
            # Arrange
            max_bytes = ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP[level]

            input_data_bytes = generate_random_bytes(NUMBER_OF_CHUNKS * max_bytes)
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
            max_bytes = ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP[level]

            input_data_bytes = generate_random_bytes(NUMBER_OF_CHUNKS * max_bytes + 1)
            configuration = QRVideoEncodingConfiguration(error_correction=level)

            # Act
            images = generate_qr_images(input_data_bytes, configuration)

            # Assert
            self.assertEqual(len(images), NUMBER_OF_CHUNKS + 1)

    def test__generate_image_frame__should__return_combined_images(self) -> None:
        for level in ERROR_CORRECT_LEVELS:
            # Arrange
            max_bytes = ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP[level]

            input_data_bytes = generate_random_bytes(NUMBER_OF_CHUNKS * max_bytes)
            configuration = QRVideoEncodingConfiguration(
                error_correction=level,
            )
            images = generate_qr_images(input_data_bytes, configuration)
            layout = GridLayout(
                size=(354, 354),
                rectangles=[(0, 0), (0, 177), (177, 0), (177, 177)],
                rectangle_indices=[0, 1, 2, 3],
            )

            # Act
            frame = generate_image_frame(images, layout)

            # Assert
            self.assertEqual(len(images), NUMBER_OF_CHUNKS)
            self.assertEqual(frame.shape[:2], layout.size)

    def test__generate_image_frames__should__return_combined_images(self) -> None:
        for level in ERROR_CORRECT_LEVELS:
            # Arrange
            max_bytes = ERROR_CORRECTION_TO_MAX_BYTES_LOOKUP[level]

            input_data_bytes = generate_random_bytes(NUMBER_OF_CHUNKS * max_bytes)
            configuration = QRVideoEncodingConfiguration(
                error_correction=level, qr_codes_per_frame=2
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
        qr_code_image_frame = pil_to_cv2(qr_code_image)

        # Act
        output_data_bytes = decode_qr_image(qr_code_image_frame)
        output_data = from_bytes(output_data_bytes)

        # Assert
        self.assertEqual(input_data, output_data)

    # endregion

    def tearDown(self):
        # Remove test file after use.
        remove_file(TEST_VIDEO_FILENAME)
