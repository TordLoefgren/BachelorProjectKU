"""
A module containing constants and definitions used by other modules in the package.
"""

from pathlib import Path
from typing import Tuple, TypeVar, Union

import numpy as np
from cv2.typing import MatLike as _matlike

# region ----- types -----


ALLOWED_TYPES = Union[bytes, float, int, str, np.ndarray]
MatLike = _matlike
T = TypeVar("T")
TSerialized = TypeVar("TSerialized")
TFrame = TypeVar("TFrame")

# endregion


# region ----- constants -----


BGR = "BGR"
RGB = "RGB"
# TODO: The max size should be determined dynamically or through the configuration.
# We set a large max size in order to experiment with multi-QR code frames.
MAX_SIZE: Tuple[int, int] = (4000, 4000)
MP4V = "mp4v"
PROJECT_DIRECTORY = Path(__file__).parent.parent
TQDM_BAR_COLOUR_GREEN = "green"
TQDM_BAR_FORMAT_STRING = "[{elapsed}<{remaining}] {n_fmt}/{total_fmt} | {l_bar}{bar} {rate_fmt}{postfix}"  # See https://www.datacamp.com/tutorial/tqdm-python.
UTF_8_ENCODING_STRING = "utf-8"


# endregion
