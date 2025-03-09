from src.base import PipelineValidationException, validate_equal_sizes
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
    try:
        output_data = pipeline.run(input_data, DEMO_FILENAME, configuration)
    except PipelineValidationException as e:
        print(f"Failure: {e}")
    else:
        print("Success!")

        # Write to output file.
        output_file_name = "output." + get_file_extension(file_name)
        write_file_as_binary(output_data, output_file_name)

    # (Optional) Remove output files.
    remove_file(DEMO_FILENAME)
    remove_file(output_file_name)


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
    )

    # Run pipeline.
    output_data = pipeline.run(input_data, DEMO_FILENAME, configuration)

    # Validate input / output.
    failed_qr_codes_readings = sum(
        1 for input in input_data if input not in output_data
    )

    # Showcase results.
    print(
        f"QR codes read correctly: {NUMBER_OF_FRAMES - failed_qr_codes_readings} / {NUMBER_OF_FRAMES}"
    )
    print("Success!" if failed_qr_codes_readings == 0 else "Failure!")

    # Remove demo video file after use.
    remove_file(DEMO_FILENAME)


if __name__ == "__main__":
    _qr_code_demo()
    # _qr_code_demo_file()
