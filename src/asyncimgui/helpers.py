from imgui_bundle import hello_imgui, imgui
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

# Technically python has no true primitives, but there are a few types that I'd like to just print out with str() rather than expand.
_primitives = (int, float, str, bool, type(None))
def show_object(id: str, title: str, obj: object, max_depth: int = 3, *, include_dunder: bool = False):
    """ 
    Displays the attributes of an object. Primitive objects will be a simple imgui.text while most objects will be a tree node with the attributes of the object. 

    :param id: String ID for the object. Should be unique under its parent widget. 
    :param title: Title string for the object. Doesn't need to be unique.
    :param obj: The object to show
    :param max_depth: Max depth of the object before it stops showing subobjects.
    :param include_dunder: Set to True to include dunder attributes. They are typically left off otherwise there will be a lot of clutter.
    """
    if type(obj) in _primitives:
        imgui.text(f"{title}: {obj.__class__.__name__} = {obj}")
    elif max_depth < 1:
        imgui.text(f"{title}: {obj.__class__.__name__} (Max depth reached)")
    elif type(obj) is list:
        if imgui.tree_node(id, f"{title}: {obj.__class__.__name__}"):
            for i, subobj in enumerate(obj):
                show_object(str(i), str(i), subobj, max_depth - 1, include_dunder=include_dunder)
            imgui.tree_pop()
    elif type(obj) is dict:
        if imgui.tree_node(id, f"{title}: {obj.__class__.__name__}"):
            for name, value in obj.items():
                show_object(str(name), str(name), value, max_depth - 1, include_dunder=include_dunder)
            imgui.tree_pop()
    elif imgui.tree_node(id, f"{title}: {obj.__class__.__name__}"):
        attributes = dir(obj)
        for attribute in attributes:
            if not include_dunder and attribute.startswith("__") and attribute.endswith("__"):
                continue

            try:
                show_object(attribute, attribute, obj.__getattribute__(attribute), max_depth - 1, include_dunder=include_dunder)
            except Exception as e:
                imgui.text(f"{attribute} - Could not retrieve attribute [{e}]")

        imgui.tree_pop()

