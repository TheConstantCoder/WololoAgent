"""PTT client entry point.

Orchestrates hotkey detection, audio capture, server communication,
and audio playback in a main event loop.
"""

import asyncio
import json
import websockets
import sys
import os

from client.hotkeys import HotkeyListener
from client.audio import Microphone, Speaker


class VoiceClient:
    """Main client class for Wololo Coach voice interaction."""

    def __init__(self, server_url: str = "ws://localhost:8000/voice"):
        self.server_url = server_url
        self.mic = Microphone()
        self.speaker = Speaker()
        self.hotkey = HotkeyListener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self.websocket = None
        self.is_running = False
        self.is_recording = False
        self.bytes_sent = 0

    def _on_press(self):
        """PTT Key Pressed."""
        if not self.is_recording:
            print("\n[LISTENING...] (Speak now)")
            self.is_recording = True
            self.bytes_sent = 0

    def _on_release(self):
        """PTT Key Released."""
        if self.is_recording:
            print(f"\n[THINKING...] (Sent {self.bytes_sent} bytes. Waiting for coach...)")
            self.is_recording = False

    async def _manual_trigger_loop(self):
        """Fallback loop for environments where hotkeys don't work."""
        print("Fallback: Press ENTER to talk (Toggle)")
        while self.is_running:
            await asyncio.to_thread(input, "")
            if not self.is_recording:
                self._on_press()
            else:
                self._on_release()

    async def _send_loop(self):
        """Loop to send audio data to server."""
        last_recording_state = False
        while self.is_running:
            # 1. Send audio chunks if recording
            if self.is_recording:
                chunks_sent = 0
                for chunk in self.mic.get_audio():
                    await self.websocket.send(chunk)
                    self.bytes_sent += len(chunk)
                    chunks_sent += 1
                
                if chunks_sent > 0:
                    print(f"\rAudio Stream: {self.bytes_sent} bytes sent", end="", flush=True)
            
            # 2. Handle state transition (Release)
            if last_recording_state and not self.is_recording:
                await self.websocket.send(json.dumps({"type": "end_of_turn"}))
            
            last_recording_state = self.is_recording
            await asyncio.sleep(0.01)

    async def _receive_loop(self):
        """Loop to receive audio data from server."""
        try:
            async for message in self.websocket:
                if isinstance(message, bytes):
                    self.speaker.play(message)
                else:
                    try:
                        data = json.loads(message)
                        if data.get("type") == "interrupted":
                            print("\n[COACH INTERRUPTED]")
                            self.speaker.clear()
                    except Exception:
                        pass
        except websockets.exceptions.ConnectionClosed:
            print("\n[CLIENT] Connection closed by server.")

    async def run(self):
        """Main execution loop."""
        print("--- Wololo Coach Client ---")
        print(f"Connecting to {self.server_url}...")
        
        try:
            async with websockets.connect(self.server_url, ping_interval=None) as ws:
                self.websocket = ws
                self.is_running = True
                
                try:
                    self.mic.start()
                    self.speaker.start()
                except Exception as e:
                    print(f"Hardware Error: {e}")
                    return

                self.hotkey.start()
                print("Connected! Hold [CTRL] or press [ENTER] to talk.")
                
                await asyncio.gather(
                    self._send_loop(),
                    self._receive_loop(),
                    self._manual_trigger_loop()
                )
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.stop()

    def stop(self):
        """Graceful shutdown."""
        self.is_running = False
        self.mic.stop()
        self.speaker.stop()
        self.hotkey.stop()
        print("\nDisconnected.")


async def main():
    client = VoiceClient()
    try:
        await client.run()
    except (KeyboardInterrupt, EOFError):
        client.stop()


if __name__ == "__main__":
    asyncio.run(main())
