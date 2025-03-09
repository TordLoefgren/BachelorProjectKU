"""
A module that contains functions used for measuring the performance of tasks.
"""

import cProfile
import pstats
from concurrent.futures import ProcessPoolExecutor, as_completed
from time import perf_counter
from typing import Callable, Iterable, List, Optional, Tuple, overload

from src.constants import TQDM_BAR_COLOUR_GREEN, TQDM_BAR_FORMAT_STRING, T
from tqdm import tqdm


@overload
def measure_task_performance_decorator(task: Callable[..., None]) -> None:
    """Overload function for tasks returning None."""
    ...


@overload
def measure_task_performance_decorator(task: Callable[..., T]) -> T:
    """Overload function for tasks returning T."""
    ...


def measure_task_performance_decorator(task: Callable[..., T]):
    """
    Function that wraps a task and times its performance, using cProfile.
    """

    def wrapper():
        with cProfile.Profile() as profile:
            task()

        results = pstats.Stats(profile)
        results.sort_stats(pstats.SortKey.TIME)
        results.print_stats()

        print(f"Task '{task.__name__}' finished in {results.total_tt:.4f} seconds.\n")

    return wrapper


@overload
def measure_task_performance(task: Callable[..., None]) -> float:
    """Overload function for tasks returning None."""
    ...


@overload
def measure_task_performance(task: Callable[..., T]) -> Tuple[T, float]:
    """Overload function for tasks returning T."""
    ...


def measure_task_performance(task: Callable[..., T]):
    """
    Function that wraps a task and times its performance.

    Returns the elapsed time in seconds, or a tuple (result, seconds) if the task returns a non-None value.
    """

    start = perf_counter()

    result = task()

    duration = perf_counter() - start

    if result is None:
        return duration

    return result, duration


def execute_parallel_tasks(
    tasks: Iterable[Callable[..., T]],
    verbose: bool = False,
    description: str = "Processing",
    max_workers: Optional[int] = None,
) -> List[T]:
    """
    A function that executes iterable tasks in parallel and returns the results in a list.
    """

    results: List[T] = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            i: executor.submit(_execute_task, task) for i, task in enumerate(tasks)
        }

        for future in tqdm(
            as_completed(futures.values()),
            total=len(futures),
            desc=description,
            disable=not verbose,
            bar_format=TQDM_BAR_FORMAT_STRING,
            colour=TQDM_BAR_COLOUR_GREEN,
        ):
            results.append(future.result())

    return [results[i] for i in sorted(futures)]


def _execute_task(task: Callable[..., T]) -> T:
    """
    Helper method that allows the process pool executor to execute callables.
    """

    return task()
