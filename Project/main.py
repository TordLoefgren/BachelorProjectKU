import os

from src.qr_codes import (
    QRVideoEncodingConfiguration,
    decode_video_to_data,
    generate_image_frames,
    generate_qr_images,
)
from src.utils import from_bytes, generate_random_string, to_bytes
from src.video_processing import create_video_from_frames

STRING_DATA_LENGTH = 30
NUMBER_OF_FRAMES = 240
DEMO_FILENAME = "demo_video.mp4"


def _qr_code_demo():
    """
    A prototype demo for QR code encoding and decoding.
    """

    # Create data.
    input_data = "".join(
        generate_random_string(STRING_DATA_LENGTH) for _ in range(NUMBER_OF_FRAMES)
    )
    input_data_bytes = bytearray()
    for data in input_data:
        input_data_bytes.extend(to_bytes(data))

    configuration = QRVideoEncodingConfiguration(
        show_decoding_window=True, chunk_size=STRING_DATA_LENGTH
    )
    # Create QR codes images from that data.
    qr_code_images = generate_qr_images(bytes(input_data_bytes), configuration)

    # Create a video with 24 QR code image frames per second, with a duration of 240 / 24 = 10 seconds.
    qr_code_frames = generate_image_frames(qr_code_images, configuration)
    create_video_from_frames(
        qr_code_frames, DEMO_FILENAME, configuration.frames_per_second
    )

    # Capture the video and decode the QR code.
    output_data_bytes = decode_video_to_data(DEMO_FILENAME, configuration)
    output_data = from_bytes(output_data_bytes)

    # Remove video file after use.
    if os.path.exists(DEMO_FILENAME):
        os.remove(DEMO_FILENAME)

    # Validate input / output.
    failed_qr_codes_readings = 0
    for input in input_data:
        if input not in output_data:
            failed_qr_codes_readings += 1

    # Print the result.
    print(
        f"QR codes read correctly: {NUMBER_OF_FRAMES - failed_qr_codes_readings} / {NUMBER_OF_FRAMES}"
    )


if __name__ == "__main__":
    _qr_code_demo()
