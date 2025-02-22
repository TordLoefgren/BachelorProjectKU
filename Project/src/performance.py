"""
A module that contains functions used for measuring the performance of tasks.
"""

from time import perf_counter
from typing import Any, Awaitable, Callable, Tuple, TypeVar, overload

T = TypeVar("T")


@overload
def measure_task_performance(task: Callable[..., None], verbose: bool = False) -> float:
    """Overload function for tasks returning None."""
    ...


@overload
def measure_task_performance(
    task: Callable[..., Any], verbose: bool = False
) -> Tuple[Any, float]:
    """Overload function for tasks returning Any."""
    ...


def measure_task_performance(task: Callable[..., T], verbose: bool = False):
    """
    Function that wraps a task and times its performance.
    """

    start = perf_counter()

    result = task()

    duration = perf_counter() - start

    if verbose:
        print(f"Performance time: {duration:.6f} seconds")

    if result is None:
        return duration

    return result, duration


@overload
async def measure_task_performance_async(
    task: Awaitable[None], verbose: bool = False
) -> float:
    """Overload function for async tasks returning None."""
    ...


@overload
async def measure_task_performance_async(
    task: Awaitable[Any], verbose: bool = False
) -> Tuple[Any, float]:
    """Overload function for async tasks returning Any."""
    ...


async def measure_task_performance_async(task: Awaitable[T], verbose: bool = False):
    """
    Function that wraps an async task and times its performance.
    """

    start = perf_counter()

    result = await task()

    duration = perf_counter() - start

    if verbose:
        print(f"Performance time: {duration:.6f} seconds")

    if result is None:
        return duration

    return result, duration
