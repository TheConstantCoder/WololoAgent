"""Audio input and output handling.

Manages recording from the microphone and playing back received audio.
"""

import queue
import sounddevice as sd
import numpy as np


class Microphone:
    """Handles microphone recording."""

    def __init__(self, sample_rate: int = 16000, chunk_size: int = 512):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.queue = queue.Queue()
        self.stream = None

    def _callback(self, indata, frames, time, status):
        """Internal callback for sounddevice."""
        if status:
            print(f"Microphone Status: {status}")
        # Convert to 16-bit PCM and put in queue
        self.queue.put(indata.copy())

    def start(self):
        """Start recording."""
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16',
            blocksize=self.chunk_size,
            callback=self._callback
        )
        self.stream.start()

    def stop(self):
        """Stop recording."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def get_audio(self):
        """Get audio chunks from the queue.
        
        Returns:
            Tuple of (bytes, peak_amplitude, rms_volume)
        """
        while not self.queue.empty():
            data = self.queue.get()
            peak = np.max(np.abs(data))
            # Calculate Root Mean Square (RMS) for more stable VAD
            rms = np.sqrt(np.mean(data.astype(np.float32)**2))
            yield data.tobytes(), peak, rms


class Speaker:
    """Handles audio playback via a byte-level buffer.

    Incoming PCM bytes are appended to a lock-protected buffer.
    The sounddevice callback drains exactly the number of frames it
    needs each invocation, eliminating chunk-size mismatches that
    cause pitch / speed distortion.
    """

    def __init__(self, sample_rate: int = 24000, blocksize: int = 960):
        self.sample_rate = sample_rate
        self.blocksize = blocksize  # 960 samples = 40 ms at 24 kHz
        self._buffer = bytearray()
        self._lock = __import__('threading').Lock()
        self.stream = None

    def _callback(self, outdata, frames, time, status):
        """Internal callback for sounddevice."""
        if status:
            print(f"Speaker Status: {status}")

        # Each frame is 1 channel × 2 bytes (int16)
        needed = frames * 2
        with self._lock:
            if len(self._buffer) >= needed:
                chunk = bytes(self._buffer[:needed])
                del self._buffer[:needed]
            else:
                # Drain whatever is left, pad the rest with silence
                chunk = bytes(self._buffer) + b'\x00' * (needed - len(self._buffer))
                self._buffer.clear()

        outdata[:] = np.frombuffer(chunk, dtype='int16').reshape(-1, 1)

    def start(self):
        """Start playback stream."""
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16',
            blocksize=self.blocksize,
            callback=self._callback,
        )
        self.stream.start()

    def stop(self):
        """Stop playback."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def play(self, pcm_bytes: bytes):
        """Append raw PCM bytes to the playback buffer."""
        with self._lock:
            self._buffer.extend(pcm_bytes)

    def is_playing(self) -> bool:
        """Check if there is audio in the buffer or currently playing."""
        with self._lock:
            return len(self._buffer) > 0

    def clear(self):
        """Clear the playback buffer (for interruptions)."""
        with self._lock:
            self._buffer.clear()
