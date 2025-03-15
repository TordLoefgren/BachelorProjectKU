"""
A module that contains functions for video processing.
"""

import time
from dataclasses import dataclass
from functools import partial
from typing import List, Optional, Tuple, Union

import cv2
import dxcam
import numpy as np
from PIL.Image import Image, fromarray
from qrcode.image.base import BaseImage
from rectpack import newPacker
from src.base import EncodingConfiguration, VideoHandler
from src.constants import (
    BGR,
    MP4V,
    RGB,
    TQDM_BAR_COLOUR_GREEN,
    TQDM_BAR_FORMAT,
    MatLike,
)
from src.performance import execute_parallel_tasks
from tqdm import tqdm


@dataclass
class GridLayout:
    size: Tuple[int, int]
    rectangles: List[Tuple[int, int]]
    rectangle_indices: List[int]


def create_video_from_frames(
    frames: List[MatLike], file_path: str, configuration: EncodingConfiguration
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

    fourcc = cv2.VideoWriter_fourcc(*MP4V)
    video_writer = cv2.VideoWriter(
        file_path, fourcc, configuration.frames_per_second, (width, height)
    )

    # Make sure that the frame is shaped correctly for the writer.
    if configuration.enable_multiprocessing:
        resized_frames = execute_parallel_tasks(
            (
                partial(resize_frame, frames[i], (width, height))
                for i in range(0, len(frames))
            ),
            max_workers=configuration.max_workers,
            verbose=configuration.verbose,
            description="Resizing frames",
        )

        for frame in resized_frames:
            video_writer.write(frame)
    else:
        for frame in tqdm(
            range(0, len(frames)),
            desc="Resizing frames",
            disable=not configuration.verbose,
            bar_format=TQDM_BAR_FORMAT,
            colour=TQDM_BAR_COLOUR_GREEN,
        ):
            frame = resize_frame(frame, (width, height))
            video_writer.write(frame)

    video_writer.release()


def create_frames_from_video(
    file_path: str,
    configuration: EncodingConfiguration,
) -> List[MatLike]:
    """
    Captures a video and returns all the frames.

    Inspiration from:
    https://stackoverflow.com/questions/18954889/how-to-process-images-of-a-video-frame-by-frame-in-video-streaming-using-openc
    """

    frames = []
    capture = cv2.VideoCapture(file_path)

    while capture.isOpened():
        ret, frame = capture.read()
        if not ret:
            break

        if configuration.show_decoding_window:
            # TODO: See if there is a way to avoid having the window block operations.
            cv2.imshow(f"Reading '{file_path}'", frame)

        if configuration.show_decoding_window and cv2.waitKey(10) & 0xFF == ord("q"):
            break

        frames.append(frame)

    capture.release()

    if configuration.show_decoding_window:
        cv2.destroyAllWindows()

    return frames


def create_frames_from_capture(
    configuration: EncodingConfiguration,
    duration_seconds: int,
    region: Optional[tuple[int, int, int, int]] = None,
) -> List[MatLike]:
    """
    Captures the screen and returns the frames.

    Utilizes the high FPS video capture package 'dxcam': https://github.com/ra1nty/DXcam

    FPS manager inspiration from:

    https://www.youtube.com/watch?v=Y-DyOdjLif4
    """

    camera = dxcam.create(output_color=BGR)
    camera.start(
        target_fps=configuration.frames_per_second, video_mode=True, region=region
    )

    prev_time = 0
    fps_display_delay = 0
    fps_delayed = 0
    fps_list = [0.0] * 10

    frames: List[MatLike] = []

    stop = time.time() + duration_seconds
    while time.time() < stop:
        frame = camera.get_latest_frame()

        if configuration.verbose:
            # Calculate the FPS
            curr_time = time.perf_counter()
            fps = 1 / (curr_time - prev_time)
            prev_time = curr_time

            # Add current FPS to a list and remove last element.
            fps_list.append(fps)
            fps_list.pop(0)

            # Get the average FPS using the last 10 frames.
            avg_fps = sum(fps_list) / len(fps_list)

            fps_display_delay += 1

            if fps_display_delay >= 3:
                fps_delayed = avg_fps
                fps_display_delay = 0

            print(f"FPS: {fps_delayed: .0f}")

        frames.append(frame)

    # Release resources.
    camera.stop()
    del camera

    return frames


@dataclass
class CV2VideoManager(VideoHandler):
    write = create_video_from_frames
    read = create_frames_from_video


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


def _pil_to_cv2(image: Union[BaseImage, Image]) -> MatLike:
    """
    Helper function that converts a PIL image to CV2 image array.

    PIL-like images are used by 'qrcode' behind the hood.

    We pre-convert the PIL image into RGB for safe conversion to CV2.

    'qrcode' GitHub page:
    https://github.com/lincolnloop/python-qrcode
    """

    if isinstance(image, (BaseImage, Image)):
        rgb_image = image.convert(RGB)
    else:
        raise TypeError(f"Unsupported data type: {type(image)}")

    image_array = np.array(rgb_image)
    cv2_image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

    return cv2_image_array


def _cv2_to_pil(cv2_image_array: MatLike) -> Image:
    """
    Helper function that converts a CV2 image array to PIL image.

    Inspiration from:
    https://www.geeksforgeeks.org/convert-opencv-image-to-pil-image-in-python/
    """

    image_array = cv2.cvtColor(np.array(cv2_image_array), cv2.COLOR_BGR2RGB)
    pil_image = fromarray(image_array)

    return pil_image


def resize_frame(frame: MatLike, size: Tuple[int, int]):
    """
    Resizes the frame according to the width and height given."""

    width, height = size

    if frame.shape[:2] != size:
        frame = cv2.resize(frame, (width, height))

    return frame
