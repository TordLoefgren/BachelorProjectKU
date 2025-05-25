from unittest import TestCase

from parameterized import parameterized
from src.constants import MatLike
from src.enums import QREncodingLibrary, QRErrorCorrectionLevel
from src.qr_configuration import QREncodingConfiguration
from src.qr_pipeline import create_qr_video_encoding_pipeline
from src.utils import generate_random_bytes, remove_file

DATA_LENGTH = 2331
MOCK_FILE_NAME = "temp.mp4"


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
            (b"Hello World", QREncodingLibrary.SEGNO),
            (b"\xff\xfe\xfd\xfa\x00\x01\xf0\xc1\xc0\x80", QREncodingLibrary.SEGNO),
            (
                b"\xc3\xa4\xc2\xbd\xc2\xa0\xc3\xa5\xc2\xa5\xc2\xbd",
                QREncodingLibrary.SEGNO,
            ),
            (b"TEST TEST!\xff\xfe\xfa\x00ABC\x00\x00\xff\xff", QREncodingLibrary.SEGNO),
            (
                b"\xed\xa0\x80\xed\xbf\xbf",
                QREncodingLibrary.SEGNO,
            ),
            (b"\xff", QREncodingLibrary.SEGNO),
            (b"\x00", QREncodingLibrary.SEGNO),
            (b"Hello World", QREncodingLibrary.QRCODE),
            (b"\xff\xfe\xfd\xfa\x00\x01\xf0\xc1\xc0\x80", QREncodingLibrary.QRCODE),
            (
                b"\xc3\xa4\xc2\xbd\xc2\xa0\xc3\xa5\xc2\xa5\xc2\xbd",
                QREncodingLibrary.QRCODE,
            ),
            (
                b"TEST TEST!\xff\xfe\xfa\x00ABC\x00\x00\xff\xff",
                QREncodingLibrary.QRCODE,
            ),
            (b"\xed\xa0\x80\xed\xbf\xbf", QREncodingLibrary.QRCODE),
            (b"\xff", QREncodingLibrary.QRCODE),
            (b"\x00", QREncodingLibrary.QRCODE),
        ]
    )
    def test__run___should__return_original_data(
        self,
        input_data: bytes,
        qr_encoding_library: QREncodingLibrary,
    ) -> None:
        configuration = QREncodingConfiguration(
            qr_encoding_library=qr_encoding_library,
            error_correction=QRErrorCorrectionLevel.H,
        )

        result = self.pipeline_default.run(
            input_data, MOCK_FILE_NAME, configuration, mock=False
        )

        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.value)
        self.assertIsNone(result.exception)
        self.assertEqual(input_data, result.value)

    def tearDown(self):
        # Remove test file after use.
        remove_file(MOCK_FILE_NAME)
