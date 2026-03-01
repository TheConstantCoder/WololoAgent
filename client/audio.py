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
        """Get audio chunks from the queue."""
        while not self.queue.empty():
            yield self.queue.get().tobytes()


class Speaker:
    """Handles audio playback."""

    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate
        self.queue = queue.Queue()
        self.stream = None

    def _callback(self, outdata, frames, time, status):
        """Internal callback for sounddevice."""
        if status:
            print(f"Speaker Status: {status}")
        
        try:
            data = self.queue.get_nowait()
            if len(data) < len(outdata):
                outdata[:len(data)] = data
                outdata[len(data):].fill(0)
            else:
                outdata[:] = data[:len(outdata)]
        except queue.Empty:
            outdata.fill(0)

    def start(self):
        """Start playback stream."""
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16',
            callback=self._callback
        )
        self.stream.start()

    def stop(self):
        """Stop playback."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def play(self, pcm_bytes: bytes):
        """Queue PCM bytes for playback."""
        # Convert bytes back to numpy int16 array
        data = np.frombuffer(pcm_bytes, dtype='int16')
        
        # Split into small chunks if needed to avoid blocking callback for too long
        # or just put in queue if it matches block size expectations
        # For simplicity, we just put it in.
        # But sounddevice callback expects 'frames' amount of data.
        # We might need to chunk it here.
        chunk_size = 512 # matching some reasonable block size
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            # Ensure chunk is the right shape (frames, channels)
            if len(chunk) < chunk_size:
                padding = np.zeros(chunk_size - len(chunk), dtype='int16')
                chunk = np.concatenate([chunk, padding])
            self.queue.put(chunk.reshape(-1, 1))

    def clear(self):
        """Clear the playback queue (for interruptions)."""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break
