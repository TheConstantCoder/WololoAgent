"""Gemini Live API voice handler.

Manages bidirectional WebSocket audio streaming with Gemini 2.5 Flash Live API.
"""

import asyncio
import json
import traceback
from typing import AsyncGenerator

from google import genai
from google.genai import types
from fastapi import WebSocket

from server.config import settings
from server.coach import coach


class VoiceHandler:
    """Handles bidirectional voice streaming between client and Gemini."""

    def __init__(self):
        # The client is initialized in Coach, we'll use that instance if possible 
        # or create a local one with the correct version.
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        self.model_id = settings.gemini_model

    async def handle_session(self, websocket: WebSocket):
        """Main loop for a voice coaching session."""
        await websocket.accept()
        print("[SERVER] Client connected.")
        
        # Grounding instruction passed in config
        config = {
            'system_instruction': coach.system_instruction,
            'response_modalities': ['AUDIO'],
        }

        try:
            print(f"[SERVER] Connecting to Gemini ({self.model_id})...")
            async with self.client.aio.live.connect(model=self.model_id, config=config) as session:
                print("[SERVER] Session established.")
                
                async def gemini_to_client():
                    try:
                        async for message in session.receive():
                            if message.server_content:
                                model_turn = message.server_content.model_turn
                                if model_turn:
                                    for part in model_turn.parts:
                                        if part.inline_data:
                                            # Forward Gemini's voice to client
                                            await websocket.send_bytes(part.inline_data.data)
                                            
                            if message.server_content and message.server_content.interrupted:
                                await websocket.send_json({"type": "interrupted"})
                    except Exception as e:
                        print(f"[SERVER] Gemini Output Error: {e}")

                async def client_to_gemini():
                    try:
                        while True:
                            message = await websocket.receive()
                            
                            if "bytes" in message:
                                # Forward audio data from client to Gemini
                                await session.send(
                                    input={"data": message["bytes"], "mime_type": "audio/pcm;rate=16000"},
                                    end_of_turn=False
                                )
                            elif "text" in message:
                                msg = json.loads(message["text"])
                                if msg.get("type") == "end_of_turn":
                                    print("[SERVER] User finished speaking. Prompting Gemini...")
                                    # Trigger model response with a textual cue
                                    await session.send(input="Please respond to the audio above.", end_of_turn=True)
                    except Exception as e:
                        print(f"[SERVER] Client Input Error: {e}")

                await asyncio.gather(gemini_to_client(), client_to_gemini())

        except Exception as e:
            print(f"[SERVER] Fatal Error: {e}")
            traceback.print_exc()
        finally:
            print("[SERVER] Session ended.")
            try:
                await websocket.close()
            except:
                pass

# Global voice handler instance
voice_handler = VoiceHandler()
