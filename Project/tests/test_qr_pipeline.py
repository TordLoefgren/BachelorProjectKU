import os
from unittest import TestCase

from src.base import PROJECT_DIRECTORY
from src.qr_pipeline import create_qr_video_encoding_pipeline
from src.utils import from_bytes, generate_random_ascii_string, remove_file, to_bytes

STRING_DATA_LENGTH = 100
TEST_DIRECTORY = PROJECT_DIRECTORY / "tests"
TEST_VIDEO_FILENAME = TEST_DIRECTORY / "test_video.mp4"


class TestQRPipeline(TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self) -> None:
        self.pipeline = create_qr_video_encoding_pipeline(
            serialize_function=to_bytes,
            deserialize_function=from_bytes,
        )

    def test__run_encode__should__create_video_file(self) -> None:
        # Arrange
        input_data = generate_random_ascii_string(STRING_DATA_LENGTH)

        # Act
        self.pipeline.run_encode(input_data, TEST_VIDEO_FILENAME)

        # Assert
        self.assertTrue(os.path.exists(TEST_VIDEO_FILENAME))

    def test__run_decode__should__return_data_from_video_file(self) -> None:
        # Arrange
        input_data = generate_random_ascii_string(STRING_DATA_LENGTH)
        self.pipeline.run_encode(input_data, TEST_VIDEO_FILENAME)

        # Act
        output_data = self.pipeline.run_decode(TEST_VIDEO_FILENAME)

        # Assert
        self.assertTrue(os.path.exists(TEST_VIDEO_FILENAME))
        self.assertEqual(input_data, output_data)

    def test__run_pipeline__should__encode_video_and_return_data(self) -> None:
        # Arrange
        input_data = generate_random_ascii_string(STRING_DATA_LENGTH)

        # Act
        output_data = self.pipeline.run(input_data, TEST_VIDEO_FILENAME)

        # Assert
        self.assertTrue(os.path.exists(TEST_VIDEO_FILENAME))
        self.assertEqual(input_data, output_data)

    def tearDown(self):
        # Remove test file after use.
        remove_file(TEST_VIDEO_FILENAME)
