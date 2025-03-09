from src.base import validate_equal_sizes
from src.qr_configuration import QREncodingConfiguration
from src.qr_pipeline import create_qr_video_encoding_pipeline
from src.utils import (
    from_bytes,
    generate_random_ascii_string,
    get_file_extension,
    open_file_dialog,
    read_file_as_binary,
    remove_file,
    to_bytes,
    write_file_as_binary,
)

CHUNK_SIZE = 1200
NUMBER_OF_FRAMES = 240
DEMO_FILENAME = "demo_video.mp4"


def _qr_code_demo_file() -> None:
    """
    A prototype demo for QR code encoding and decoding - choose file manually.
    """

    # Get data.
    file_name = open_file_dialog()
    input_data = read_file_as_binary(file_name)

    # Build pipeline.
    configuration = QREncodingConfiguration(verbose=True)
    pipeline = create_qr_video_encoding_pipeline(
        serialize_function=None,
        deserialize_function=None,
        validate_function=validate_equal_sizes,
    )

    # Run pipeline.
    result = pipeline.run(input_data, DEMO_FILENAME, configuration, mock=True)
    if result.is_valid:
        # Write to output file.
        output_file_name = "output." + get_file_extension(file_name)
        write_file_as_binary(result.value, output_file_name)

        # Remove output file.
        remove_file(output_file_name)
    else:
        print(result.exception)

    # Remove video file after use.
    remove_file(DEMO_FILENAME)


def _qr_code_demo() -> None:
    """
    A prototype demo for QR code encoding and decoding.
    """

    # Get data.
    input_data = generate_random_ascii_string(CHUNK_SIZE * NUMBER_OF_FRAMES)

    # Build pipeline.
    configuration = QREncodingConfiguration(
        chunk_size=CHUNK_SIZE,
        show_decoding_window=True,
        verbose=True,
    )
    pipeline = create_qr_video_encoding_pipeline(
        serialize_function=to_bytes,
        deserialize_function=from_bytes,
        validate_function=validate_equal_sizes,
    )

    # Run pipeline.
    result = pipeline.run(input_data, DEMO_FILENAME, configuration)
    if not result.is_valid:
        print(result.exception)

    # Remove video file after use.
    remove_file(DEMO_FILENAME)


if __name__ == "__main__":
    _qr_code_demo()
    # _qr_code_demo_file()
