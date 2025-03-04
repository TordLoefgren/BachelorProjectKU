from pathlib import Path

from src.enums import QRErrorCorrectLevels
from src.performance import measure_task_performance
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


def _qr_code_demo():
    """
    A prototype demo for QR code encoding and decoding.
    """

    print("Running a QR encoding pipeline demo...\n")

    # Create data.
    input_data = generate_random_string(CHUNK_SIZE * NUMBER_OF_FRAMES)

    # Build pipeline.
    configuration = QRVideoEncodingConfiguration(
        show_decoding_window=True, chunk_size=CHUNK_SIZE
    )
    pipeline = create_qr_video_encoding_pipeline(configuration=configuration)

    # Run pipeline.
    print("Encoding...")
    encode_duration = measure_task_performance(
        lambda: pipeline.run_encode(input_data, DEMO_FILENAME)
    )
    print(f"Finished in {encode_duration:.4f} seconds.\n")

    print("Decoding...")
    output_data, decode_duration = measure_task_performance(
        lambda: pipeline.run_decode(input_data, DEMO_FILENAME)
    )
    print(f"Finished in {decode_duration:.4f} seconds.\n")

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

    file_name = Path(open_file_dialog())

    pipeline = create_qr_video_encoding_pipeline(
        serialize_function=None,
        deserialize_function=None,
        configuration=QRVideoEncodingConfiguration(
            error_correction=QRErrorCorrectLevels.ERROR_CORRECT_H,
            enable_parallelization=False,
        ),
    )

    print("--- Running QR encoding pipeline ---\n")

    input = read_file_as_binary(Path(file_name))

    # Run pipeline.
    print("Encoding...")
    encode_duration = measure_task_performance(
        lambda: pipeline.run_encode(input, DEMO_FILENAME)
    )
    print(f"Finished encoding in {encode_duration:.4f} seconds.\n")

    print("Decoding...\n")
    output, decode_duration = measure_task_performance(
        lambda: pipeline.run_decode(DEMO_FILENAME)
    )
    print(f"Finished decoding in {decode_duration:.4f} seconds.\n\n")

    print(len(input) == len(output))

    write_file_as_binary(output, Path("output.pdf"))

    print(
        f"Finished pipeline roundtrip after {encode_duration + decode_duration:.4f} seconds."
    )
