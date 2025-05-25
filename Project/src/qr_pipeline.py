"""
A module that contains logic relating to the creation of QR video encoding pipelines.
"""

from dataclasses import dataclass

from src.base import (
    Base64Serializer,
    Encoder,
    Serializer,
    ValidationFunction,
    VideoEncodingPipeline,
    VideoHandler,
    validate_equals,
)
from src.qr_decoding import decode_frames_to_data
from src.qr_encoding import encode_data_to_frames
from src.video_processing import CV2VideoHandler


@dataclass
class QREncoder(Encoder):
    encode = encode_data_to_frames
    decode = decode_frames_to_data


def create_qr_video_encoding_pipeline(
    serializer: Serializer = Base64Serializer,
    encoder: Encoder = QREncoder,
    video_handler: VideoHandler = CV2VideoHandler,
    validation_function: ValidationFunction = validate_equals,
) -> VideoEncodingPipeline:
    """
    Creates an instance of the QR code video encoding pipeline.
    """

    return VideoEncodingPipeline(
        serializer=serializer,
        encoder=encoder,
        video_handler=video_handler,
        validation_function=validation_function,
    )
