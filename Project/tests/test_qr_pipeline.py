from unittest import TestCase

from parameterized import parameterized
from src.constants import MatLike
from src.qr_configuration import QREncodingConfiguration
from src.qr_pipeline import create_qr_video_encoding_pipeline
from src.utils import generate_random_bytes, remove_file

DATA_LENGTH = 100
MOCK_FILE_NAME = "mock.mp4"


class TestQRPipeline(TestCase):

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self) -> None:
        self.pipeline_default = create_qr_video_encoding_pipeline()
        self.configuration_default = QREncodingConfiguration()

    def test__encode__should__return_frames(self) -> None:
        # Arrange
        input_data = generate_random_bytes(DATA_LENGTH)

        # Act
        frames = self.pipeline_default.encode(input_data, self.configuration_default)

        # Assert
        self.assertIsInstance(frames[0], MatLike)

    def test__decode__should__return_data_from_frames(self) -> None:
        # Arrange
        input_data = generate_random_bytes(DATA_LENGTH)
        frames = self.pipeline_default.encode(input_data, self.configuration_default)

        # Act
        output_data = self.pipeline_default.decode(
            self.configuration_default, frames=frames
        )

        # Assert
        self.assertEqual(input_data, output_data)

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
    def test__run___should__return_original_data(self, input_data) -> None:
        # Arrange & Act
        result = self.pipeline_default.run(
            input_data, MOCK_FILE_NAME, self.configuration_default, mock=True
        )

        # Assert
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.value)
        self.assertIsNone(result.exception)
        self.assertEqual(input_data, result.value)

    def tearDown(self):
        # Remove test file after use.
        remove_file(MOCK_FILE_NAME)
