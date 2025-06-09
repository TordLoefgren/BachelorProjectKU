"""
A module containing constants and definitions used by other modules in the package.
"""

from pathlib import Path

from cv2.typing import MatLike as _matlike

# region ----- types -----


MatLike = _matlike

# endregion

# region ----- constants -----

BYTE_TO_MB = 1 / (1024**2)
SEED = 42
MILLISECONDS_PER_SECOND = 1000
CONFIGURATION_HEADER_LENGTH_BYTES = 4
BYTE_ORDER_BIG = "big"
BGR = "BGR"
RGB = "RGB"
MP4V = "mp4v"
FFV1 = "FFV1"
PROJECT_DIRECTORY = Path(__file__).parent.parent
TQDM_BAR_COLOUR_GREEN = "green"
TQDM_BAR_FORMAT = (
    "[{elapsed}<{remaining}] {n_fmt}/{total_fmt} | {l_bar}{bar} {rate_fmt}{postfix}"
)
UTF_8_ENCODING = "utf-8"


# endregion
