from imgui_bundle import imgui, hello_imgui
from collections.abc import Callable

class DockingLayoutBuilder:
    def __init__(self, name: str, direction: imgui.Dir, ratio: float, node_flags: imgui.DockNodeFlags_ | None = None) -> None:
        self.name = name
        self.direction = direction
        self.ratio = ratio
        self.node_flags = node_flags
        self.children: list[DockingLayoutBuilder] = []
        self.windows: list[hello_imgui.DockableWindow] = []

    def add_split(self, name: str, direction: imgui.Dir, ratio: float, node_flags: imgui.DockNodeFlags_ | None = None) -> "DockingLayoutBuilder":
        if name == "MainDockSpace":
            raise ValueError("MainDockSpace cannot be a child of a split.")

        split = DockingLayoutBuilder(name, direction, ratio, node_flags)
        self.children.append(split)
        return split
    
    def add_window(self, label: str, gui_function: Callable[[], None], is_visible: bool = True, can_be_closed: bool = True) -> hello_imgui.DockableWindow:
        window = hello_imgui.DockableWindow(
            label_=label, 
            dock_space_name_=self.name, 
            gui_function_=gui_function, 
            is_visible_=is_visible, 
            can_be_closed_=can_be_closed)
        self.windows.append(window)
        return window
    
    def build_splits(self) -> list[hello_imgui.DockingSplit]:
        splits = []
        if self.name != "MainDockSpace":
            splits.append(hello_imgui.DockingSplit(
            initial_dock_="MainDockSpace", 
            new_dock_=self.name,
            direction_=self.direction,
            ratio_=self.ratio,
            node_flags_=self.node_flags
        ))
        for child in self.children:
            child_splits = child.build_splits()
            # Assuming that the first entry in the list is always the root of the subtree.
            child_splits[0].initial_dock = self.name
            splits += child_splits

        return splits
    
    def build_windows(self) -> list[hello_imgui.DockableWindow]:
        windows = self.windows.copy()
        for child in self.children:
            windows.extend(child.build_windows())
        return windows
    
    def attach_to_layout(self, layout: hello_imgui.DockingParams):
        layout.docking_splits = self.build_splits()
        layout.dockable_windows = self.build_windows()
    
def create_main_split() -> DockingLayoutBuilder:
    return DockingLayoutBuilder("MainDockSpace", imgui.Dir.down, 0.5)
    