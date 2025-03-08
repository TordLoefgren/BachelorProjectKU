from src.base import PipelineValidationException
from src.qr_configuration import QREncodingConfiguration
from src.qr_pipeline import create_qr_video_encoding_pipeline
from src.utils import (
    from_bytes,
    generate_random_ascii_string,
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
    configuration = QREncodingConfiguration(
        enable_parallelization=True, verbose=True, validate=True
    )
    pipeline = create_qr_video_encoding_pipeline(
        serialize_function=None,
        deserialize_function=None,
        configuration=configuration,
        validation_function=lambda input, output: len(input) == len(output),
    )

    # Run pipeline.
    try:
        output_data = pipeline.run(input_data, DEMO_FILENAME)
    except PipelineValidationException as e:
        print(f"Failure: {e}")
    else:
        print("Success!")

        # Write to output file.
        output_file_name = "output." + file_name.split(".")[-1]
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
        enable_parallelization=True,
        chunk_size=CHUNK_SIZE,
        show_decoding_window=True,
        verbose=True,
    )
    pipeline = create_qr_video_encoding_pipeline(
        serialize_function=to_bytes,
        deserialize_function=from_bytes,
        configuration=configuration,
    )

    # Run pipeline.
    output_data = pipeline.run(input_data, DEMO_FILENAME)
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
