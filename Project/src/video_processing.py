"""
A module that contains functions for video processing.
"""

from dataclasses import dataclass
from typing import List, Tuple, Union

import cv2
import numpy as np
from cv2.typing import MatLike
from PIL.Image import Image, fromarray
from qrcode.image.base import BaseImage
from rectpack import newPacker


@dataclass
class GridLayout:
    size: Tuple[int, int]
    rectangles: List[Tuple[int, int]]
    rectangle_indices: List[int]


def create_video_from_frames(
    frames: List[MatLike],
    file_path: str,
    frames_per_second: int = 24,
) -> None:
    """
    Create a video from a list of image frames.

    Inspiration from:
    https://www.tutorialspoint.com/opencv_python/opencv_python_video_images.htm
    """

    if not frames:
        return

    # Extract reference frame to determine the video image dimensions.
    reference_frame = frames[0]
    height, width = reference_frame.shape[:2]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_writer = cv2.VideoWriter(
        file_path, fourcc, frames_per_second, (width, height)
    )

    for frame in frames:
        # Make sure that the frame is shaped correctly for the writer.
        if frame.shape[:2] != (height, width):
            frame = cv2.resize(frame, (width, height))

        video_writer.write(frame)

    video_writer.release()


def create_frames_from_video(
    file_path: str,
    show_window: bool = False,
) -> List[MatLike]:
    """
    Captures a video and returns all the frames.

    Inspiration from:
    https://stackoverflow.com/questions/18954889/how-to-process-images-of-a-video-frame-by-frame-in-video-streaming-using-openc
    """

    # TODO: Returning all frames is very neat, but maybe not the most performant solution. Reconsider.
    frames = []
    capture = cv2.VideoCapture(file_path)

    while capture.isOpened():
        ret, frame = capture.read()
        if not ret:
            break

        if show_window:
            cv2.imshow(f"Reading '{file_path}'", frame)

        if show_window and cv2.waitKey(10) & 0xFF == ord("q"):
            break

        frames.append(frame)

    capture.release()

    if show_window:
        cv2.destroyAllWindows()

    return frames


def get_grid_layout(
    bin: Tuple[int, int], rectangles: List[Tuple[int, int]]
) -> GridLayout:
    """
    Computes the optimal X and Y coordinates for a list of rectangles within a given size constraint.

    Using examples from: https://github.com/secnot/rectpack

    Each rectangle is given an index as a unique identifier, maintaing its initial list ordering.
    """

    packer = newPacker()

    for i, rect in enumerate(rectangles):
        packer.add_rect(*rect, rid=i)

    packer.add_bin(*bin)

    packer.pack()

    abin = packer[0]

    layout = GridLayout(
        size=(abin.width, abin.height),
        rectangles=[(rect.x, rect.y) for rect in abin],
        rectangle_indices=[rect.rid for rect in abin],
    )

    return layout


def pil_to_cv2(image: Union[BaseImage, Image]) -> MatLike:
    """
    Helper function that converts a PIL image to CV2 image array.

    PIL-like images are used by 'qrcode' behind the hood.

    We pre-convert the PIL image into RGB for safe conversion to CV2.

    'qrcode' GitHub page:
    https://github.com/lincolnloop/python-qrcode
    """

    if isinstance(image, (BaseImage, Image)):
        rgb_image = image.convert("RGB")
    else:
        raise TypeError(f"Unsupported data type: {type(image)}")

    image_array = np.array(rgb_image)
    cv2_image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

    return cv2_image_array


def cv2_to_pil(cv2_image_array: MatLike) -> Image:
    """
    Helper function that converts a CV2 image array to PIL image.

    Inspiration from:
    https://www.geeksforgeeks.org/convert-opencv-image-to-pil-image-in-python/
    """

    image_array = cv2.cvtColor(np.array(cv2_image_array), cv2.COLOR_BGR2RGB)
    pil_image = fromarray(image_array)

    return pil_image
