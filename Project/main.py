from src.enums import QRPackage
from src.qr_codes import QRVideoEncodingConfiguration, create_qr_video_encoding_pipeline
from src.utils import (
    generate_random_string,
    open_file_dialog,
    read_file_as_binary,
    remove_file,
    write_file_as_binary,
)

CHUNK_SIZE = 30
NUMBER_OF_FRAMES = 240
DEMO_FILENAME = "demo_video.mp4"


def _qr_code_demo_manual() -> None:
    """
    A prototype demo for QR code encoding and decoding - choose file manually.
    """

    # Get data.
    file_name = open_file_dialog()
    input_data = read_file_as_binary(file_name)

    # Build pipeline.
    configuration = QRVideoEncodingConfiguration(
        enable_parallelization=True, qr_package=QRPackage.SEGNO, verbose=True
    )
    pipeline = create_qr_video_encoding_pipeline(
        serialize_function=None, deserialize_function=None, configuration=configuration
    )

    # Run pipeline.
    pipeline.run_encode(input_data, DEMO_FILENAME)
    output_data = pipeline.run_decode(DEMO_FILENAME)

    # Showcase results.
    print(f"Bytes read correctly: {len(output_data)} / {len(input_data)}")
    print("Success!" if len(output_data) == len(input_data) else "Failure!")

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
    input_data = generate_random_string(CHUNK_SIZE * NUMBER_OF_FRAMES)

    # Build pipeline.
    configuration = QRVideoEncodingConfiguration(
        show_decoding_window=True, chunk_size=CHUNK_SIZE, verbose=True
    )
    pipeline = create_qr_video_encoding_pipeline(configuration=configuration)

    # Run pipeline.
    pipeline.run_encode(input_data, DEMO_FILENAME)
    output_data = pipeline.run_decode(DEMO_FILENAME)

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
    # _qr_code_demo()
    _qr_code_demo_manual()
