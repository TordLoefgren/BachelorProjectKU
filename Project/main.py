import os

from src.base import from_bytes, generate_random_string, to_bytes
from src.qr_codes import (
    decode_qr_video_to_data,
    encode_qr_data_to_video,
    generate_qr_code_image,
)

STRING_DATA_LENGTH = 30
NUMBER_OF_FRAMES = 240
DEMO_FILENAME = "demo_video.mp4"


def _qr_code_demo():
    """
    A prototype demo for QR code encoding and decoding.
    """

    # Create data.
    input_data = [
        generate_random_string(STRING_DATA_LENGTH) for _ in range(NUMBER_OF_FRAMES)
    ]
    input_data_bytes = map(to_bytes, input_data)

    # Create QR codes images from that data.
    qr_codes_image = [generate_qr_code_image(data) for data in input_data_bytes]

    # Create a video with 24 QR code image frames per second, with a duration of 240 / 24 = 10 seconds.
    encode_qr_data_to_video(qr_codes_image, DEMO_FILENAME)

    # Capture the video and decode the QR code.
    output_data_bytes = decode_qr_video_to_data(DEMO_FILENAME, show_window=True)
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
