from imgui_bundle import hello_imgui
import logging

_log_level_map = {
    logging.DEBUG: hello_imgui.LogLevel.debug,
    logging.INFO: hello_imgui.LogLevel.info,
    logging.WARN: hello_imgui.LogLevel.warning,
    logging.ERROR: hello_imgui.LogLevel.error
}
class ImguiLogHandler(logging.Handler):
    """ A simple log handler that sends log records to hello_imgui so it shows up with the hello_imgui.log_gui component """
    def __init__(self, level: int | str = 0) -> None:
        super().__init__(level)

    def emit(self, record: logging.LogRecord) -> None:
        hello_imgui.log(_log_level_map.get(record.levelno, hello_imgui.LogLevel.info), self.format(record))