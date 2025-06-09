"""
A module that contains functions for video processing.
"""

import time
from dataclasses import dataclass
from functools import partial
from itertools import tee
from typing import Iterator, List, Optional, Tuple, Union

import cv2
import dxcam
import numpy as np
from PIL.Image import Image
from qrcode.image.base import BaseImage
from src.base import EncodingConfiguration, VideoHandler
from src.constants import (
    BGR,
    MP4V,
    RGB,
    TQDM_BAR_COLOUR_GREEN,
    TQDM_BAR_FORMAT,
    MatLike,
)
from src.performance import execute_parallel_iter_tasks
from tqdm import tqdm

# region ----- Video read / write -----


def create_video_from_frames(
    frames: Iterator[MatLike], file_path: str, configuration: EncodingConfiguration
) -> None:
    """
    Create a video from a list of image frames.

    Inspiration from:
    https://www.tutorialspoint.com/opencv_python/opencv_python_video_images.htm
    """

    # Extract reference frame to determine the video image dimensions.
    frames, peek = tee(frames)

    try:
        reference_frame = next(peek)
    except StopIteration:
        return

    height, width = reference_frame.shape[:2]

    fourcc = cv2.VideoWriter_fourcc(*MP4V)
    video_writer = cv2.VideoWriter(
        file_path,
        fourcc,
        configuration.frames_per_second,
        (width, height),
        isColor=True,
    )

    # Make sure that the frame is shaped correctly for the writer.
    if configuration.enable_multiprocessing:
        resized_frames = execute_parallel_iter_tasks(
            (partial(resize_frame, frame, (width, height)) for frame in frames),
            length=None,
            max_workers=configuration.max_workers,
            verbose=configuration.verbose,
            description="Resizing frames",
        )
    else:
        resized_frames = (
            resize_frame(frame, (width, height))
            for frame in tqdm(
                frames,
                desc="Resizing frames",
                disable=not configuration.verbose,
                bar_format=TQDM_BAR_FORMAT,
                colour=TQDM_BAR_COLOUR_GREEN,
            )
        )

    for frame in resized_frames:
        video_writer.write(frame)

    video_writer.release()


def create_frames_from_video(
    file_path: str,
    configuration: Optional[EncodingConfiguration] = None,
) -> Iterator[MatLike]:
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

        if configuration is not None:
            if configuration.show_decoding_window:
                cv2.imshow(f"Reading '{file_path}'", frame)

            if configuration.show_decoding_window and cv2.waitKey(10) & 0xFF == ord(
                "q"
            ):
                break

        frames.append(frame)

    capture.release()

    if configuration is not None and configuration.show_decoding_window:
        cv2.destroyAllWindows()

    return iter(frames)


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
class CV2VideoHandler(VideoHandler):
    write = create_video_from_frames
    read = create_frames_from_video


# region ----- Image and frame helpers -----


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


def resize_frame(frame: MatLike, size: Tuple[int, int]):
    """
    Resizes the frame according to the width and height given."""

    width, height = size

    if frame.shape[:2] != size:
        frame = cv2.resize(frame, (width, height))

    return frame


# endregion
