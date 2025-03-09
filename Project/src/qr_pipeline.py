"""
A module that contains logic relating to the creation of QR video encoding pipelines.
"""

from typing import Optional

from src.base import (
    DeserializeFunction,
    ReadVideoFunction,
    SerializeFunction,
    ValidateFunction,
    VideoEncodingPipeline,
    WriteVideoFunction,
)
from src.qr_decoding import decode_frames_to_data
from src.qr_encoding import encode_data_to_frames
from src.video_processing import create_frames_from_video, create_video_from_frames


def create_qr_video_encoding_pipeline(
    write_video_function: WriteVideoFunction = create_video_from_frames,
    read_video_function: ReadVideoFunction = create_frames_from_video,
    serialize_function: Optional[SerializeFunction] = None,
    deserialize_function: Optional[DeserializeFunction] = None,
    validate_function: Optional[ValidateFunction] = None,
) -> VideoEncodingPipeline:
    """
    Creates an instance of the QR code video encoding pipeline.
    """

    return VideoEncodingPipeline(
        encode_function=encode_data_to_frames,
        decode_function=decode_frames_to_data,
        write_video_function=write_video_function,
        read_video_function=read_video_function,
        serialize_function=serialize_function,
        deserialize_function=deserialize_function,
        validate_function=validate_function,
    )
