"""
A module that contains functions used for measuring the performance of tasks.
"""

from concurrent.futures import ProcessPoolExecutor
from time import perf_counter
from typing import (
    Any,
    Awaitable,
    Callable,
    Iterable,
    List,
    Optional,
    Tuple,
    TypeVar,
    overload,
)

T = TypeVar("T")


@overload
def measure_task_performance(task: Callable[..., None]) -> float:
    """Overload function for tasks returning None."""
    ...


@overload
def measure_task_performance(task: Callable[..., Any]) -> Tuple[Any, float]:
    """Overload function for tasks returning Any."""
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


@overload
async def measure_task_performance_async(task: Awaitable[None]) -> float:
    """Overload function for async tasks returning None."""
    ...


@overload
async def measure_task_performance_async(task: Awaitable[Any]) -> Tuple[Any, float]:
    """Overload function for async tasks returning Any."""
    ...


async def measure_task_performance_async(task: Awaitable[T]):
    """
    Function that wraps an async task and times its performance.

    Returns the elapsed time in seconds, or a tuple (result, seconds) if the task returns a non-None value.
    """

    start = perf_counter()

    result = await task()

    duration = perf_counter() - start

    if result is None:
        return duration

    return result, duration


def execute_parallel_tasks(
    tasks: Iterable[Callable[..., T]], max_workers: Optional[int] = None
) -> List[T]:
    """
    A function that executes tasks in parallel and returns the results.
    """

    results: List[T]

    with ProcessPoolExecutor(max_workers) as executor:
        results = executor.map(_run_task, tasks)

    return results


def _run_task(task: Callable[..., T]) -> T:
    """
    Helper method that allows the executor in execute_parallel_tasks to execute functions in its map function.
    """

    return task()
