import json
import numpy as np
import uuid6
from DPGWidgets.NodeEditor.node import InputNodeAttribute, OutputNodeAttribute, Node, NodeType
import dearpygui.dearpygui as dpg
import pyaudio

formats = [
    ["Float32", pyaudio.paFloat32, np.float32],
    ["Int16", pyaudio.paInt16, np.int16]
]

class AudioIOManager:
    def __init__(self):
        # UUIDs for input device controls
        self.input_device_uuid = uuid6.uuid7().hex
        self.input_channels_uuid = uuid6.uuid7().hex
        self.input_rate_uuid = uuid6.uuid7().hex
        self.input_chunk_uuid = uuid6.uuid7().hex
        self.input_format_uuid = uuid6.uuid7().hex

        # UUIDs for output device controls
        self.output_device_uuid = uuid6.uuid7().hex
        self.output_channels_uuid = uuid6.uuid7().hex
        self.output_rate_uuid = uuid6.uuid7().hex
        self.output_format_uuid = uuid6.uuid7().hex

        # Status text UUIDs
        self.input_status_uuid = uuid6.uuid7().hex
        self.output_status_uuid = uuid6.uuid7().hex

        # Default settings
        self.input_settings = {
            "device": 0,
            "channels": 2,
            "rate": 48000,
            "chunk_size": 1024,
            "format": 0
        }

        self.output_settings = {
            "device": 0,
            "channels": 2,
            "rate": 48000,
            "format": 0
        }

        self.is_init_window = False

        self.devices_input = []
        self.devices_output = []

        self.refresh_devices()


    def refresh_devices(self):
        """Refresh the audio device list"""
        pa = pyaudio.PyAudio()
        info = pa.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        self.devices_input.clear()
        self.devices_output.clear()

        for i in range(0, numdevices):
            if pa.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
                self.devices_input.append([pa.get_device_info_by_host_api_device_index(0, i).get('name'), i])
            elif pa.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels') > 0:
                self.devices_output.append([pa.get_device_info_by_host_api_device_index(0, i).get('name'), i])

        pa.terminate()

        # Update combo boxes
        if self.is_init_window:
            if dpg.does_item_exist(self.input_device_uuid):
                dpg.configure_item(self.input_device_uuid, items=[item[0] for item in self.devices_input])
            if dpg.does_item_exist(self.output_device_uuid):
                dpg.configure_item(self.output_device_uuid, items=[item[0] for item in self.devices_output])

    def update_input_settings(self):
        """Callback to update input device settings"""
        try:
            device_name = dpg.get_value(self.input_device_uuid)
            result = 0
            for d in self.devices_input:
                if d[0] == device_name:
                    result = d[1]
                    break
            self.input_settings["device"] = result
            self.input_settings["channels"] = dpg.get_value(self.input_channels_uuid)
            self.input_settings["rate"] = dpg.get_value(self.input_rate_uuid)
            self.input_settings["chunk_size"] = dpg.get_value(self.input_chunk_uuid)
            format_name = dpg.get_value(self.input_format_uuid)
            self.input_settings["format"] = 0 if "Float32" in format_name else 1
            self.save(None, None)
            dpg.set_value(self.input_status_uuid, "✓ Input settings updated")
        except Exception as e:
            dpg.set_value(self.input_status_uuid, f"✗ Error: {str(e)}")

    def update_output_settings(self):
        """Callback to update output device settings"""
        try:
            device_name = dpg.get_value(self.output_device_uuid)
            result = 0
            for d in self.devices_output:
                if d[0] == device_name:
                    result = d[1]
                    break

            self.output_settings["device"] = result
            self.output_settings["channels"] = dpg.get_value(self.output_channels_uuid)
            self.output_settings["rate"] = dpg.get_value(self.output_rate_uuid)
            format_name = dpg.get_value(self.output_format_uuid)
            self.output_settings["format"] = 0 if "Float32" in format_name else 1
            self.save(None, None)
            dpg.set_value(self.output_status_uuid, "✓ Output settings updated")
        except Exception as e:
            dpg.set_value(self.output_status_uuid, f"✗ Error: {str(e)}")

    def window(self):
        with dpg.window(label="Audio IO Manager", tag="AIOM", width=700, height=450, no_close=True):
            dpg.add_text("Audio Device Configuration", color=(100, 200, 255))
            dpg.add_separator()

            with dpg.collapsing_header(label="Input Devices", default_open=True):
                with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True,
                               borders_innerV=True, borders_outerV=True, row_background=True):
                    dpg.add_table_column(label="Setting")
                    dpg.add_table_column(label="Value")

                    with dpg.table_row():
                        dpg.add_text("Device")
                        dpg.add_combo([item[0] for item in self.devices_input], tag=self.input_device_uuid, width=300,
                                      default_value=self.devices_input[0][0] if self.devices_input else "")

                    with dpg.table_row():
                        dpg.add_text("Channels")
                        dpg.add_input_int(tag=self.input_channels_uuid, width=300,
                                          min_value=1, max_value=8, min_clamped=True, max_clamped=True,
                                          default_value=self.input_settings["channels"])

                    with dpg.table_row():
                        dpg.add_text("Sample Rate (Hz)")
                        dpg.add_input_int(tag=self.input_rate_uuid, width=300,
                                          min_value=8000, max_value=192000, min_clamped=True, max_clamped=True,
                                          default_value=self.input_settings["rate"])

                    with dpg.table_row():
                        dpg.add_text("Chunk Size (samples)")
                        dpg.add_input_int(tag=self.input_chunk_uuid, width=300,
                                          min_value=64, max_value=8192, min_clamped=True, max_clamped=True,
                                          default_value=self.input_settings["chunk_size"])

                    with dpg.table_row():
                        dpg.add_text("Format")
                        dpg.add_combo([f[0] for f in formats], tag=self.input_format_uuid, width=300,
                                      default_value=formats[self.input_settings["format"]][0])

                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Apply Input Settings", callback=lambda: self.update_input_settings(),
                                   width=200)
                    dpg.add_text("", tag=self.input_status_uuid, color=(100, 255, 100))

            dpg.add_spacer(height=10)

            with dpg.collapsing_header(label="Output Devices", default_open=True):
                with dpg.table(header_row=True, borders_innerH=True, borders_outerH=True,
                               borders_innerV=True, borders_outerV=True, row_background=True):
                    dpg.add_table_column(label="Setting")
                    dpg.add_table_column(label="Value")

                    with dpg.table_row():
                        dpg.add_text("Device")
                        dpg.add_combo([item[0] for item in self.devices_output], tag=self.output_device_uuid, width=300,
                                      default_value=self.devices_output[0][0] if self.devices_output else "")

                    with dpg.table_row():
                        dpg.add_text("Channels")
                        dpg.add_input_int(tag=self.output_channels_uuid, width=300,
                                          min_value=1, max_value=8, min_clamped=True, max_clamped=True,
                                          default_value=self.output_settings["channels"])

                    with dpg.table_row():
                        dpg.add_text("Sample Rate (Hz)")
                        dpg.add_input_int(tag=self.output_rate_uuid, width=300,
                                          min_value=8000, max_value=192000, min_clamped=True, max_clamped=True,
                                          default_value=self.output_settings["rate"])

                    with dpg.table_row():
                        dpg.add_text("Format")
                        dpg.add_combo([f[0] for f in formats], tag=self.output_format_uuid, width=300,
                                      default_value=formats[self.output_settings["format"]][0])

                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    dpg.add_button(label="Apply Output Settings", callback=lambda: self.update_output_settings(),
                                   width=200)
                    dpg.add_text("", tag=self.output_status_uuid, color=(100, 255, 100))

            dpg.add_spacer(height=10)
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_button(label="Refresh Devices", callback=lambda: self.refresh_devices(), width=150)
                dpg.add_text(f"Input devices: {len(self.devices_input)} | Output devices: {len(self.devices_output)}")
            dpg.add_text("Please restart software after changed.", color=(255, 255, 0))

        self.load(None, None)
        self.is_init_window = True

    def get_input_settings(self):
        """Return current input settings"""
        return self.input_settings.copy()

    def get_output_settings(self):
        """Return current output settings"""
        return self.output_settings.copy()

    def save(self, _, __):
        data = self.export_settings()
        json.dump(data, open("io.json", "w"))

    def load(self, _, __):
        data = json.load(open("io.json", "r"))
        self.import_settings(data)

    def export_settings(self):
        """Export all settings as a dictionary"""
        settings_dict = {
            "input": self.input_settings.copy(),
            "output": self.output_settings.copy(),
            "version": "1.0"
        }
        return settings_dict

    def import_settings(self, settings_dict):
        """Import settings from a dictionary"""
        try:
            if "input" in settings_dict:
                # Validate and update input settings
                input_data = settings_dict["input"]
                self.input_settings["device"] = input_data.get("device", 0)
                self.input_settings["channels"] = input_data.get("channels", 2)
                self.input_settings["rate"] = input_data.get("rate", 48000)
                self.input_settings["chunk_size"] = input_data.get("chunk_size", 1024)
                self.input_settings["format"] = input_data.get("format", 0)

                # Update UI elements
                if dpg.does_item_exist(self.input_device_uuid) and self.input_settings["device"] < len(self.devices_input):
                    dpg.set_value(self.input_device_uuid, self.devices_input[self.input_settings["device"]][0])
                if dpg.does_item_exist(self.input_channels_uuid):
                    dpg.set_value(self.input_channels_uuid, self.input_settings["channels"])
                if dpg.does_item_exist(self.input_rate_uuid):
                    dpg.set_value(self.input_rate_uuid, self.input_settings["rate"])
                if dpg.does_item_exist(self.input_chunk_uuid):
                    dpg.set_value(self.input_chunk_uuid, self.input_settings["chunk_size"])
                if dpg.does_item_exist(self.input_format_uuid):
                    dpg.set_value(self.input_format_uuid, formats[self.input_settings["format"]][0])

            if "output" in settings_dict:
                # Validate and update output settings
                output_data = settings_dict["output"]
                self.output_settings["device"] = output_data.get("device", 0)

                self.output_settings["channels"] = output_data.get("channels", 2)
                self.output_settings["rate"] = output_data.get("rate", 48000)
                self.output_settings["format"] = output_data.get("format", 0)

                result_display = 0
                for i, d in enumerate(self.devices_output):
                    if d[1] == self.output_settings["device"]:
                        result_display = i
                        break

                # Update UI elements
                if dpg.does_item_exist(self.output_device_uuid) and result_display < len(
                        self.devices_output):
                    dpg.set_value(self.output_device_uuid, self.devices_output[result_display][0])
                if dpg.does_item_exist(self.output_channels_uuid):
                    dpg.set_value(self.output_channels_uuid, self.output_settings["channels"])
                if dpg.does_item_exist(self.output_rate_uuid):
                    dpg.set_value(self.output_rate_uuid, self.output_settings["rate"])
                if dpg.does_item_exist(self.output_format_uuid):
                    dpg.set_value(self.output_format_uuid, formats[self.output_settings["format"]][0])

            return True, "Settings imported successfully"
        except Exception as e:
            return False, f"Error importing settings: {str(e)}"

audio_manager = AudioIOManager()

class AudioSource(Node):
    @staticmethod
    def factory(name, data):
        return AudioSource(name, data)

    def __init__(self, name, data):
        super().__init__(name, data, NodeType.INPUT)

        input_device_settings = audio_manager.get_input_settings()

        self.device_index = input_device_settings["device"]
        self.format = formats[input_device_settings["format"]]
        self.channel = input_device_settings["channels"]
        self.frame_size = input_device_settings["chunk_size"]
        self.rate = input_device_settings["rate"]

        self.apply_output_attr()

        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=self.format[1], channels=self.channel, rate=self.rate, input=True, frames_per_buffer=self.frame_size, input_device_index=self.device_index)

    def apply_output_attr(self):
        for ch in range(self.channel):
            self.add_output_attribute(OutputNodeAttribute(f"Channel {ch}"), dynamic=True)

    def process(self, data):
        if not self.stream:
            self.onCreate()

        if self._output_attributes and self.stream:
            arr = np.frombuffer(self.stream.read(self.frame_size, exception_on_overflow=False), dtype=self.format[2])
            total_samples = arr.size // self.channel
            arr = arr[:total_samples * self.channel]

            arr = arr.reshape(total_samples, self.channel)

            for ch in range(self.channel):
                try:
                    self._output_attributes[ch].set_data((arr[:, ch].copy(), self.rate, self.frame_size))
                except:
                    pass

    def __del__(self):
        if self.stream:
            self.stream.close()
            self.pa.terminate()

class AudioSink(Node):
    @staticmethod
    def factory(name, data):
        return AudioSink(name, data)

    def __init__(self, name, data):
        super().__init__(name, data, NodeType.OUTPUT)

        output_device_settings = audio_manager.get_output_settings()

        self.device_index = output_device_settings["device"]
        self.format = formats[output_device_settings["format"]]
        self.channel = output_device_settings["channels"]
        self.rate = output_device_settings["rate"]

        self.apply_input_attr()

        self.pa = pyaudio.PyAudio()

        self.stream = self.pa.open(
            format=self.format[1],
            channels=self.channel,
            rate=self.rate,
            output=True,
            output_device_index=self.device_index
        )

    def apply_input_attr(self):
        for ch in range(self.channel):
            self.add_input_attribute(InputNodeAttribute(f"Channel {ch}"), dynamic=True)

    def process(self, data):
        if not self.stream:
            self.onCreate()

        if not self._input_attributes or not self.stream:
            return

        # Collect all input channel data
        channel_data = []
        max_len = 0

        for ch in range(self.channel):
            if ch < len(self._input_attributes):
                data = self._input_attributes[ch].get_data()
                if data:
                    ch_data, sample_rate, chunksize = data

                    if ch_data is not None and len(ch_data) > 0:
                        channel_data.append(ch_data)
                        max_len = max(max_len, len(ch_data))

        if not channel_data or max_len == 0:
            return

        # Pad all channels to same length
        for i in range(len(channel_data)):
            if len(channel_data[i]) < max_len:
                channel_data[i] = np.pad(channel_data[i], (0, max_len - len(channel_data[i])))

        # Stack channels
        audio_array = np.column_stack(channel_data)  # Shape: (samples, input_channels)

        # Matrix mixing: downmix or upmix to output channels
        if audio_array.shape[1] != self.channel:
            output_array = np.zeros((audio_array.shape[0], self.channel), dtype=self.format[2])

            if self.channel == 1:
                # Downmix to mono: average all channels
                output_array[:, 0] = np.mean(audio_array, axis=1)
            elif self.channel == 2 and audio_array.shape[1] == 1:
                # Upmix mono to stereo: duplicate
                output_array[:, 0] = audio_array[:, 0]
                output_array[:, 1] = audio_array[:, 0]
            audio_array = output_array

        # Interleave channels for output
        output_data = audio_array.astype(self.format[2]).flatten()

        # Write to stream
        self.stream.write(output_data.tobytes())

    def __del__(self):
        if self.stream:
            self.stream.close()
            self.pa.terminate()