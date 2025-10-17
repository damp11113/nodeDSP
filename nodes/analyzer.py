import dearpygui.dearpygui as dpg
import numpy as np
from DPGWidgets.NodeEditor.node import InputNodeAttribute, Node, NodeType
import threading
from collections import deque


class SpectrumView(Node):
    @staticmethod
    def factory(name, data):
        return SpectrumView(name, data)

    def __init__(self, name, data):
        super().__init__(name, data, NodeType.INPUT)

        self.add_input_attribute(InputNodeAttribute("Input"))

        self.series_tag = dpg.generate_uuid()
        self.smoothed_fft = None
        self.smoothing_factor = 0.5

        # Buffer for storing audio samples
        self.buffer_duration = 0.2  # Store 0.5 seconds of audio
        self.audio_buffer = deque()
        self.max_buffer_samples = 0
        self.sample_rate = None

        # Threading
        self.processing_thread = None
        self.thread_running = False
        self.lock = threading.Lock()
        self.latest_data = None

    def custom(self):
        with dpg.plot(label="Spectrum", height=300, width=520):
            dpg.add_plot_legend()

            x = dpg.add_plot_axis(dpg.mvXAxis, label="Frequency (Hz)")
            dpg.set_axis_limits_auto(x)

            y = dpg.add_plot_axis(dpg.mvYAxis, label="Magnitude (dB)")
            dpg.set_axis_limits(y, -120, 10)

            # Add line series for FFT data
            dpg.add_line_series([], [], label="FFT", parent=y, tag=self.series_tag)

    def _processing_loop(self):
        """Background thread for FFT processing"""
        while self.thread_running:
            with self.lock:
                data_to_process = self.latest_data
                self.latest_data = None

            if data_to_process is not None:
                try:
                    audio_data, sample_rate, chunksize = data_to_process

                    # Initialize buffer size on first run
                    if self.sample_rate is None:
                        self.sample_rate = sample_rate
                        self.max_buffer_samples = int(self.buffer_duration * sample_rate)

                    # Add new audio to buffer
                    self.audio_buffer.extend(audio_data)

                    # Trim buffer to max size
                    while len(self.audio_buffer) > self.max_buffer_samples:
                        self.audio_buffer.popleft()

                    # Only process if we have enough samples
                    if len(self.audio_buffer) >= self.max_buffer_samples // 2:
                        # Convert buffer to numpy array
                        buffer_array = np.array(self.audio_buffer)

                        # Apply window function to reduce spectral leakage
                        window = np.hanning(len(buffer_array))
                        windowed_data = buffer_array * window

                        # Compute FFT with larger buffer
                        fft_data = np.fft.fft(windowed_data)

                        # Take only positive frequencies
                        n = len(fft_data)
                        fft_data = np.abs(fft_data[:n // 2])

                        # Normalize
                        fft_data = fft_data * 2.0 / n
                        fft_data[0] = fft_data[0] / 2.0

                        # Get corresponding frequencies
                        freqs = np.fft.fftfreq(n, 1.0 / sample_rate)[:n // 2]

                        # Apply exponential smoothing
                        if self.smoothed_fft is None or len(self.smoothed_fft) != len(fft_data):
                            self.smoothed_fft = fft_data
                        else:
                            self.smoothed_fft = (self.smoothing_factor * self.smoothed_fft +
                                                 (1 - self.smoothing_factor) * fft_data)

                        # Convert to dB scale
                        epsilon = 1e-10
                        fft_db = 20 * np.log10(self.smoothed_fft + epsilon)

                        # Clip values
                        fft_db = np.clip(fft_db, -120, 10)

                        # Update plot on main thread
                        if dpg.does_item_exist(self.series_tag):
                            dpg.set_value(self.series_tag, [freqs.tolist(), fft_db.tolist()])

                except Exception as e:
                    print(f"SpectrumView processing error: {e}")
            else:
                # Sleep briefly if no data to process
                threading.Event().wait(0.01)

    def process(self, data):
        # Get audio data from input
        data = self._input_attributes[0].get_data()

        if data is None or len(data) == 0:
            return

        # Start processing thread if not running
        if not self.thread_running:
            self.thread_running = True
            self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.processing_thread.start()

        # Store latest data for processing
        with self.lock:
            self.latest_data = data

    def __del__(self):
        """Cleanup when node is deleted"""
        self.stop_thread()

    def stop_thread(self):
        """Stop the processing thread"""
        if self.thread_running:
            self.thread_running = False
            if self.processing_thread is not None:
                self.processing_thread.join(timeout=1.0)
                self.processing_thread = None