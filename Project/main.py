from src.qr_configuration import QREncodingConfiguration
from src.qr_video_encoder import QRVideoEncoder
from src.utils import open_file_dialog, read_file_as_binary, write_file_as_binary

if __name__ == "__main__":

    # Read file as binary.
    file_name = open_file_dialog()
    input_data = read_file_as_binary(file_name)

    # Create configuration and encoder.
    config = QREncodingConfiguration(verbose=True)
    encoder = QRVideoEncoder(config)

    # Encode and decode in a single step.
    result = encoder.roundtrip(input_data, file_path="demo_video.mp4")

    if result.is_valid:
        # Create a 1:1 copy of the input text.
        write_file_as_binary(result.value, "output.txt")
    else:
        print("Decoding failed:", result.exception)
