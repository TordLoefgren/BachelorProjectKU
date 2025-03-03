from src.performance import measure_task_performance
from src.qr_codes import QRVideoEncodingConfiguration, create_qr_video_encoding_pipeline
from src.utils import generate_random_string, remove_file

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
        lambda: pipeline.run_pipeline(input_data, DEMO_FILENAME)
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
    _qr_code_demo()
