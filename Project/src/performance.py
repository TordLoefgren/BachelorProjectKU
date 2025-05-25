"""
A module that contains functions used for measuring the performance of tasks.
"""

from concurrent.futures import ProcessPoolExecutor
from time import perf_counter
from typing import Callable, Dict, Iterable, List, Optional, Tuple, overload

from src.constants import (
    MILLISECONDS_PER_SECOND,
    TQDM_BAR_COLOUR_GREEN,
    TQDM_BAR_FORMAT,
)
from tqdm import tqdm

# region ----- Multiprocessing -----


def execute_parallel_tasks[T](
    tasks: Iterable[Callable[..., T]],
    length: int,
    verbose: bool = False,
    description: str = "Processing",
    max_workers: Optional[int] = None,
) -> List[T]:
    """
    Executes iterable tasks in parallel and returns the ordered results in a list.
    """

    results: Dict[int, T] = {}

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(
            tqdm(
                executor.map(_execute_task, tasks),
                total=length,
                desc=description,
                disable=not verbose,
                bar_format=TQDM_BAR_FORMAT,
                colour=TQDM_BAR_COLOUR_GREEN,
            )
        )

    return results


def _execute_task[T](task: Callable[..., T]) -> T:
    """
    Helper method that allows the process pool executor to execute callables.
    """

    return task()


# endregion

# region ----- Performance -----


@overload
def measure_task_performance(task: Callable[..., None]) -> float:
    """Overload function for tasks returning None."""
    ...


@overload
def measure_task_performance[T](task: Callable[..., T]) -> Tuple[T, float]:
    """Overload function for tasks returning T."""
    ...


def measure_task_performance[T](task: Callable[..., T]):
    """
    Function that wraps a task and times its performance.

    Returns the elapsed time in seconds, or a tuple (result, seconds) if the task returns a non-None value.
    """

    start = perf_counter()

    result = task()

    duration_ms = (perf_counter() - start) * MILLISECONDS_PER_SECOND

    if result is None:
        return duration_ms

    return result, duration_ms


# endregion
