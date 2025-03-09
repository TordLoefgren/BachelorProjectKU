import os
from unittest import TestCase

from src.constants import PROJECT_DIRECTORY, MatLike
from src.qr_configuration import QREncodingConfiguration
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
        self.pipeline_default = create_qr_video_encoding_pipeline(
            serialize_function=to_bytes,
            deserialize_function=from_bytes,
        )
        self.configuration_default = QREncodingConfiguration()

    def test__run_encode__should__return_frames(self) -> None:
        # Arrange
        input_data = generate_random_ascii_string(STRING_DATA_LENGTH)

        # Act
        frames = self.pipeline_default.run_encode(
            input_data, self.configuration_default
        )

        # Assert
        self.assertIsInstance(frames[0], MatLike)

    def test__run_decode__should__return_data_from_frames(self) -> None:
        # Arrange
        input_data = generate_random_ascii_string(STRING_DATA_LENGTH)
        frames = self.pipeline_default.run_encode(
            input_data, self.configuration_default
        )

        # Act
        output_data = self.pipeline_default.run_decode(
            frames, self.configuration_default
        )

        # Assert
        self.assertEqual(input_data, output_data)

    def test__run_pipeline__should__encode_video_and_return_data(self) -> None:
        # Arrange
        input_data = generate_random_ascii_string(STRING_DATA_LENGTH)

        # Act
        result = self.pipeline_default.run(
            input_data, TEST_VIDEO_FILENAME, self.configuration_default
        )

        # Assert
        self.assertIsNotNone(result.value)
        self.assertIsNone(result.exception)
        self.assertTrue(os.path.exists(TEST_VIDEO_FILENAME))
        self.assertEqual(input_data, result.value)

    def tearDown(self):
        # Remove test file after use.
        remove_file(TEST_VIDEO_FILENAME)
