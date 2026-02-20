from imgui_bundle import imgui, hello_imgui
from asyncimgui import helpers, ImguiApp, TaskTracker
import logging
import asyncio
from dataclasses import dataclass

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[helpers.ImguiLogHandler()],
    format="%(asctime)s %(levelname)s > %(message)s"
)

@dataclass
class AppState:
    """ 
    `asyncimgui` does not track app-specific state. 
    For simpler apps, a few module-level variables may be all you need. 
    This example has a class that's instantiated and pass into the gui methods via the main method.
    """
    task_tracker: TaskTracker | None = None
    counter: int = 0

logger = logging.getLogger(__name__)

async def long_running_coroutine():
    while True:
        await asyncio.sleep(1)
        logger.info("Long running task")

async def sleep_then_log(time: float):
    await asyncio.sleep(time)
    logger.info("Short asnyc coroutine")

def main_window(app: ImguiApp, state: AppState):
    imgui.text("Hello world!")
    imgui.text("This is the main window.")
    imgui.text(f"Frames passed: {state.counter}")

    if imgui.button("Create a log record"):
        logger.info("Hello!")
    if imgui.button("Short blocking task"):
        app.schedule_coroutine(sleep_then_log(1), blocking=True)
    if imgui.button("Short non-blocking task"):
        task_id, state.task_tracker = app.schedule_coroutine(sleep_then_log(1))
        logger.info(f"Task started with task id: {task_id}")
    if state.task_tracker is not None:
        imgui.text("Non-blocking task done" if state.task_tracker.task.done() else "Non-blocking task ongoing")
        

def app_window(app: ImguiApp):
    imgui.separator_text("Task Trackers")
    for id, tracker in app.task_trackers.items():
        imgui.text(f"{id}: {tracker.task.get_name()}, blocking={tracker.blocking}")


async def main():
    app = ImguiApp()
    app_state = AppState()

    async def on_update(dt: float):
        app_state.counter += 1

    app.callbacks.on_update = on_update

    # Creating the splits and their windows
    main_split = helpers.create_main_split()
    main_split.add_window("Main", lambda: main_window(app, app_state))
    main_split.add_split("AppSpace", imgui.Dir.right, 0.5).add_window("App", lambda: app_window(app))
    main_split.add_split("LoggerSpace", imgui.Dir.down, 0.25).add_window("Logs", hello_imgui.log_gui)

    runner_params = hello_imgui.RunnerParams()
    runner_params.app_window_params.window_title="Example"
    runner_params.imgui_window_params.show_menu_bar=True
    main_split.attach_to_layout(runner_params.docking_params)
    runner_params.imgui_window_params.default_imgui_window_type = hello_imgui.DefaultImGuiWindowType.provide_full_screen_dock_space

    app.schedule_coroutine(long_running_coroutine())   
    await app.run(runner_params)
    # This point will only be reached once the app has shut down.
    # You may want to put the run call in a try-finally block if you need additional graceful shutdown steps.

if __name__ == "__main__":
    asyncio.run(main())