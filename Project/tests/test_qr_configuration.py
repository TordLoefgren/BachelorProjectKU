import unittest

from src.qr_configuration import QREncodingConfiguration


class TestQRConfiguration(unittest.TestCase):

    def setUp(self) -> None:
        self.original_config = QREncodingConfiguration(
            enable_multiprocessing=True,
            frames_per_second=30,
            show_decoding_window=True,
            verbose=True,
            chunk_size=512,
            max_workers=4,
        )

    def test__to_bytes_should__serialize_without_error(self) -> None:
        # Arrange & Act
        result = QREncodingConfiguration.to_bytes(self.original_config)

        # Assert
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)

    def test__from_bytes_should__deserialize_to_configuration_object(self) -> None:
        # Arrange
        serialized = QREncodingConfiguration.to_bytes(self.original_config)

        # Act
        deserialized = QREncodingConfiguration.from_bytes(serialized)

        # Assert
        self.assertEqual(self.original_config, deserialized)

    def test__from_bytes_should__return_new_configuration_instance(self) -> None:
        # Arrange
        serialized = QREncodingConfiguration.to_bytes(self.original_config)

        # Act
        deserialized = QREncodingConfiguration.from_bytes(serialized)
        deserialized.frames_per_second = 60

        # Assert
        self.assertNotEqual(
            self.original_config.frames_per_second, deserialized.frames_per_second
        )

    def test__from_bytes_should__raise_exception_if_input_is_invalid(self) -> None:
        # Arrange
        invalid_data = b"I am pickle Rick!"

        # Act / Assert
        with self.assertRaises(Exception):
            QREncodingConfiguration.from_bytes(invalid_data)
