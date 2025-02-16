import os

from src.base import from_base64, generate_random_string, to_base64
from src.qr_codes import (
    generate_qr_code_image,
    generate_qr_code_sequence_video,
    read_qr_code_sequence_video,
)

STRING_DATA_LENGTH = 30
NUMBER_OF_FRAMES = 240

if __name__ == "__main__":
    # ----- Short prototype demo ----

    # Create data.
    input_data = [
        generate_random_string(STRING_DATA_LENGTH) for _ in range(NUMBER_OF_FRAMES)
    ]
    base_64_input_data = [to_base64(data) for data in input_data]

    # Create QR codes images from that data.
    qr_codes_image = [generate_qr_code_image(text) for text in base_64_input_data]

    # Create a video with 24 QR code image frames per second, with a duration of 240 / 24 = 10 seconds.
    file_name = "demo_video.mp4"
    generate_qr_code_sequence_video(qr_codes_image, file_name)

    # Capture the video and decode the QR code.
    base_64_output_data = read_qr_code_sequence_video(file_name, show_window=True)
    output_data = [from_base64(data, is_string=True) for data in base_64_output_data]

    # Remove video file after use.
    if os.path.exists(file_name):
        os.remove(file_name)

    # Validate input / output.
    failed_qr_codes_readings = 0
    for input in input_data:
        if input not in output_data:
            failed_qr_codes_readings += 1

    # Print the result.
    print(
        f"QR codes read correctly: {NUMBER_OF_FRAMES - failed_qr_codes_readings} / {NUMBER_OF_FRAMES}"
    )
