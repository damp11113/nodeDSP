import json
import time
from threading import Thread

import dearpygui.dearpygui as dpg
import uuid6

from DPGWidgets.NodeEditor.widget import NodeEditor, DragSourceContainer, DragSource
from DPGWidgets.NodeEditor.node import NodeManager

from nodes import audioio, analyzer

class Nodeditor:
    def __init__(self):
        #self.effects_contaniar = DragSourceContainer("Effects", 150, -1)
        self.IO_container = DragSourceContainer("Nodes", 150, -1)

        self.left_panel = uuid6.uuid7().hex

        nm = NodeManager()

        self.node_editor = NodeEditor(nm)

        nm.register("AIN", audioio.AudioSource.factory)
        nm.register("AOUT", audioio.AudioSink.factory)

        nm.register("STV", analyzer.SpectrumView.factory)

        self.IO_container.add_drag_source(DragSource("Audio Source", "AIN", None, "I/O"))
        self.IO_container.add_drag_source(DragSource("Audio Sink", "AOUT", None, "I/O"))
        self.IO_container.add_drag_source(DragSource("Spectrum", "STV", None, "Viewer"))

    def save(self, _, __):
        data = self.node_editor.save()
        json.dump(data, open("ne.json", "w"))

    def load(self, _, __):
        data = json.load(open("ne.json", "r"))
        self.node_editor.load(data)

    def widget(self, parent):
        with dpg.group(id=self.left_panel, parent=parent):
            self.IO_container.submit(self.left_panel)

        # center panel
        self.node_editor.submit(parent, width=-1)

class App:
    def __init__(self):
        self.ne = Nodeditor()
        self.is_running = False
        self.process_time = 0
        self.last_window_size = (0, 0)

    def window(self):
        with dpg.window(label="Node Editor", tag="nodewindow", width=500, height=320, no_close=True):
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="Save", callback=self.ne.save)
                    dpg.add_menu_item(label="Load", callback=self.ne.load)

            dpg.add_group(tag="nodeeditor", horizontal=True)

    def menubar(self):
        with dpg.viewport_menu_bar(tag="menubar"):
            with dpg.menu(label="File"):
                dpg.add_spacer()
                dpg.add_menu_item(label="Exit", callback=lambda: self.exit())

            dpg.add_text(f"Processing Time: ???", tag="menubar_status")

    def on_mouse_click(self, sender, app_data):
        self.ne.node_editor.on_mouse_click(sender, app_data)

    def on_key_press(self, sender, key):
        self.ne.node_editor.on_key_press(sender, key)

    def working_thread(self):
        while self.is_running:
            starttime = time.time()
            try:
                self.ne.node_editor.process(None)
            except Exception as e:
                pass

            self.process_time = time.time() - starttime

    def init(self):
        dpg.create_context()
        dpg.create_viewport(title='NodeDSP', width=1280, height=720)  # set viewport window
        dpg.setup_dearpygui()
        # -------------- add code here --------------
        with dpg.handler_registry():
            dpg.add_mouse_click_handler(callback=self.on_mouse_click)
            dpg.add_key_press_handler(callback=self.on_key_press)

        #dpg.configure_app(docking=True, docking_space=True)
        dpg.configure_app(init_file="workspace.ini")

        self.window()
        self.menubar()
        audioio.audio_manager.window()

        self.ne.widget("nodeeditor")

        # -------------------------------------------
        dpg.show_viewport()

        self.is_running = True
        ta = Thread(target=self.working_thread, daemon=True)
        ta.start()

        while dpg.is_dearpygui_running():
            self.render()
            dpg.render_dearpygui_frame()

        self.exit()

    def render(self):
        window_width = dpg.get_viewport_width()
        window_height = dpg.get_viewport_height()

        if self.last_window_size != (window_width, window_height):
            dpg.set_item_pos("menubar_status", [dpg.get_viewport_width() - 200, 0])

        dpg.set_value("menubar_status", f"Processing Time: {self.process_time*1000:.2f}ms")

    def exit(self):
        dpg.destroy_context()


app = App()
app.init()
