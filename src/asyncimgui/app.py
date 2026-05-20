from __future__ import annotations
import asyncio
from asyncio import Task
import time
import logging
from collections.abc import Coroutine, Awaitable, Callable
from typing import Any
from dataclasses import dataclass

from imgui_bundle import hello_imgui

logger = logging.getLogger(__name__)

class NoImguiAppError(Exception):
    pass

_app: ImguiApp | None = None

def get_current_app() -> ImguiApp:
    if _app is None:
        raise NoImguiAppError("There is no ImguiApp in context. This method can only be run in GUI functions and in on_update.")
    return _app

def schedule(tracker: TaskTracker) -> int:
    return get_current_app().schedule(tracker) 

def schedule_coroutine(coroutine: Coroutine | Task, blocking: bool = False, name: str | None = None) -> tuple[int, TaskTracker]:
    return get_current_app().schedule_coroutine(coroutine, blocking, name) 

@dataclass
class AppCallbacks:
    """ All the callbacks for `ImguiApp` """

    # Called before rendering but after runner params are set up.
    on_start: Callable[[], Any] | None = None
    # Called before tasks are processed for the update and prior to rendering.
    # The float passed in is time passed between the last frame and this one.
    on_update: Callable[[float], Any] | None = None
    # Called prior to shutdown.
    on_shutdown: Callable[[], Any] | None = None

class TaskTracker:
    def __init__(self, coroutine: Coroutine | Task, blocking: bool = False, name: str | None = None) -> None:
        if isinstance(coroutine, Task):
            self.task = coroutine
        else:
            self.task = asyncio.create_task(coroutine, name=name)
        self.blocking = blocking
        self.time_created = time.monotonic()

class ImguiApp:
    """
    Helps handle async tasks and an async update loop with hello_imgui.
    Call `run` to start the loop. Method will return when the program shuts down.
    If an async task needs to be run from a rendering call, schedule it via `schedule`. There's also `schedule_coroutine` as a convenience.    
    """

    def __init__(self) -> None:
        self.callbacks = AppCallbacks()
        self.task_trackers: dict[int, TaskTracker] = {}
        # How long a frame can take before a warning is logged.
        # Setting to 0 or a negative value disables it.
        self.delta_time_warning_limit = 0.5  

        self._task_id = 0
        self._monotonic_time = time.monotonic()

    def _get_task_id(self) -> int:
        self._task_id += 1
        return self._task_id

    async def _update(self):
        global _app

        now = time.monotonic()
        elapsed_time = now - self._monotonic_time
        self._monotonic_time = now
        if self.delta_time_warning_limit > 0 and elapsed_time > self.delta_time_warning_limit:
            logger.warning(f"Frame took an abnormal amount of time ({elapsed_time} seconds).")

        if self.callbacks.on_update is not None:
            try:
                _app = self
                self.callbacks.on_update(elapsed_time)
                _app = None
            except Exception as e:
                logger.exception(e)

        blocking_tasks = []
        to_remove = []
        for id, tracker in self.task_trackers.items():
            if tracker.blocking:
                blocking_tasks.append(tracker.task)
                to_remove.append(id)
            elif tracker.task.done():
                to_remove.append(id)

        for id in to_remove:
            self.task_trackers.pop(id)

        results = await asyncio.gather(*blocking_tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.exception(result)
            elif isinstance(result, asyncio.CancelledError):
                pass
            elif isinstance(result, BaseException):
                # BaseExceptions should end the program, they're things like KeyboardInterrupts and should propagate.
                raise

    async def _cancel_tasks(self):
        for tracker in self.task_trackers.values():
            tracker.task.cancel()

        results = [await asyncio.gather(*[tracker.task for tracker in self.task_trackers.values()], return_exceptions=True)]
        for result in results:
            if isinstance(result, Exception):
                logger.exception(result)
            elif isinstance(result, asyncio.CancelledError):
                pass
            elif isinstance(result, BaseException):
                # BaseExceptions should end the program, they're things like KeyboardInterrupts and should propagate.
                raise

    async def run(self, runner_params: hello_imgui.RunnerParams):
        global _app

        hello_imgui.manual_render.setup_from_runner_params(runner_params)
        if self.callbacks.on_start is not None:
            returned = self.callbacks.on_start()
            if isinstance(returned, Awaitable):
                # on_start throwing an exception shouldn't start the program since it's likely to be in an invalid state at this point.
                # Don't catch, just let it raise.
                await returned

        self._monotonic_time = time.monotonic()
        try:
            while not hello_imgui.get_runner_params().app_shall_exit:
                await self._update()
                _app = self
                hello_imgui.manual_render.render()
                _app = None
                await asyncio.sleep(0) # Give background tasks time to complete.
        finally:
            if self.callbacks.on_shutdown is not None:
                try:
                    returned = self.callbacks.on_shutdown()
                    if isinstance(returned, Awaitable):
                        await returned
                except Exception as e:
                    logger.exception(e)
            await self._cancel_tasks()
            hello_imgui.manual_render.tear_down()

    def shutdown(self):
        # Simplest way to shutdown is to set this flag and then just let it shut down naturally on the next update.
        hello_imgui.get_runner_params().app_shall_exit = True

    def schedule(self, tracker: TaskTracker) -> int:
        """ Schedules a task tracker to the app. """
        task_id = self._get_task_id()
        self.task_trackers[self._get_task_id()] = tracker
        return task_id
    
    def schedule_coroutine(self, coroutine: Coroutine | Task, blocking: bool = False, name: str | None = None) -> tuple[int, TaskTracker]:
        """ Convenience method for scheduling coroutines. Wraps the given coroutine/task in a TaskTracker, schedules it, and then returns the TaskTracker. """
        task_id = self._get_task_id()
        tracker = TaskTracker(coroutine=coroutine, blocking=blocking, name=name)
        self.task_trackers[self._get_task_id()] = tracker
        return task_id, tracker