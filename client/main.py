"""Hands-free VAD client.

Automatically detects speech using volume thresholds and streams
to the Wololo Coach server.
"""

import asyncio
import json
import signal
import time

import websockets

from client.audio import Microphone, Speaker

# --- VAD CONFIG ---
SILENCE_THRESHOLD = 350.0  # RMS volume above this triggers "speaking"
SILENCE_DURATION = 0.8    # SNAPPY: Seconds of silence before turn ends
# ------------------

class VoiceClient:
    def __init__(self, server_url: str = "ws://localhost:8000/voice"):
        self.server_url = server_url
        self.mic = Microphone()
        self.speaker = Speaker()
        self.websocket = None
        self.is_running = False
        self.is_recording = False
        self.last_voice_time = 0
        self.bytes_sent = 0
        self.bytes_received = 0
        self._shutdown_event = asyncio.Event()

    async def _manual_trigger_loop(self):
        print("\n--- Wololo Coach (Hands-Free Mode) ---")
        print(f"VAD Threshold: {SILENCE_THRESHOLD} | Silence Timeout: {SILENCE_DURATION}s")
        print("Just speak to start | Type a question + ENTER for text")
        print("Ctrl+C to quit\n")

        while self.is_running:
            try:
                user_input = await asyncio.to_thread(input, "> ")
            except (EOFError, OSError):
                break
            if user_input.strip() != "":
                print(f"[SENDING TEXT]: {user_input}")
                await self.websocket.send(json.dumps({"type": "text_query", "text": user_input}))

    async def _send_loop(self):
        while self.is_running:
            for chunk, peak, rms in self.mic.get_audio():
                now = time.time()
                is_speaker_active = self.speaker.is_playing()
                
                # --- VAD Logic with Feedback Suppression ---
                dynamic_threshold = SILENCE_THRESHOLD
                if is_speaker_active:
                    dynamic_threshold = SILENCE_THRESHOLD * 5.0
                
                if rms > dynamic_threshold:
                    if not self.is_recording:
                        print("\n[VOICE DETECTED]")
                        self.is_recording = True
                        self.bytes_sent = 0
                    self.last_voice_time = now
                else:
                    # INSTANT ECHO KILL: 
                    # If the speaker is active and the mic is just hearing the speaker (rms < 5x threshold),
                    # we must NOT be in a recording state, otherwise Gemini hears an echo.
                    if is_speaker_active and self.is_recording:
                        self.is_recording = False
                
                if self.is_recording:
                    await self.websocket.send(chunk)
                    self.bytes_sent += len(chunk)
                    
                    # Update volume meter
                    meter_len = 20
                    level = int((min(rms, 2000) / 2000) * meter_len)
                    meter = "█" * level + "-" * (meter_len - level)
                    status = "SPEAKER ACTIVE" if is_speaker_active else "LISTENING"
                    print(f"\rVAD ({status}): [{meter}] {rms:>6.1f} RMS | Sent: {self.bytes_sent} bytes", end="", flush=True)

                    # Check for silence timeout
                    if now - self.last_voice_time > SILENCE_DURATION:
                        print(f"\n[SILENCE — Turn ended] (Sent {self.bytes_sent} bytes)")
                        self.is_recording = False

            await asyncio.sleep(0.01)

    async def _receive_loop(self):
        async for message in self.websocket:
            if isinstance(message, bytes):
                self.bytes_received += len(message)
                self.speaker.play(message)
            else:
                data = json.loads(message)
                if data.get("type") == "interrupted":
                    print("\n[COACH INTERRUPTED]")
                    self.speaker.clear()

    async def run(self):
        print(f"Connecting to {self.server_url}...")
        loop = asyncio.get_running_loop()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._shutdown_event.set)

        try:
            async with websockets.connect(self.server_url, ping_interval=None) as ws:
                self.websocket = ws
                self.is_running = True
                self.mic.start()
                self.speaker.start()

                tasks = [
                    asyncio.create_task(self._send_loop(), name="send"),
                    asyncio.create_task(self._receive_loop(), name="receive"),
                    asyncio.create_task(self._manual_trigger_loop(), name="input"),
                ]

                shutdown_task = asyncio.create_task(self._shutdown_event.wait(), name="shutdown")
                done, _ = await asyncio.wait(
                    tasks + [shutdown_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                self.is_running = False
                for t in tasks:
                    t.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                shutdown_task.cancel()

        except Exception as e:
            if not self._shutdown_event.is_set():
                print(f"Error: {e}")
        finally:
            await self.stop()

    async def stop(self):
        self.is_running = False
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
        self.mic.stop()
        self.speaker.stop()
        print("\nDisconnected.")

if __name__ == "__main__":
    try:
        asyncio.run(VoiceClient().run())
    except KeyboardInterrupt:
        pass
