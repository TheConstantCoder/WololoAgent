"""Gemini Live API voice handler.

Streams audio between a local WebSocket client and the Gemini Multimodal
Live API.  The key insight is that ``session.receive()`` yields messages
for **one model turn only** (it breaks after ``turn_complete``).  We
therefore wrap it in an outer ``while True`` so the receiver loops back
and picks up every subsequent turn.
"""

import asyncio
import json
import traceback
from google import genai
from google.genai import types
from fastapi import WebSocket
from server.config import settings
from server.coach import coach


class VoiceHandler:
    def __init__(self):
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
            http_options={'api_version': 'v1alpha'}
        )
        self.model_id = settings.gemini_model

    async def handle_session(self, websocket: WebSocket):
        await websocket.accept()
        print("[SERVER] Client connected.")

        config = types.LiveConnectConfig(
            system_instruction=types.Content(
                parts=[types.Part(text=coach.system_instruction)]
            ),
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Aoede'
                    )
                )
            ),
        )

        try:
            async with self.client.aio.live.connect(
                model=self.model_id, config=config
            ) as session:
                print("[SERVER] Gemini connection established.")

                # --- Gemini → Client ----------------------------------------
                async def gemini_to_client():
                    """Read model responses and forward audio to the client.

                    ``session.receive()`` is an async-iterator that breaks
                    after each ``turn_complete``.  The outer ``while True``
                    re-enters it so we keep listening for every new turn.
                    """
                    try:
                        while True:  # <-- re-enter receive() after each turn
                            async for message in session.receive():
                                if websocket.client_state.value == 3:  # DISCONNECTED
                                    break

                                # DEBUG: packet flags
                                has_content = message.server_content is not None
                                has_setup  = message.setup_complete is not None
                                has_meta   = message.usage_metadata is not None
                                print(
                                    f"[DEBUG] Gemini Msg | Content: {has_content}"
                                    f" | Setup: {has_setup} | Meta: {has_meta}"
                                )

                                if message.server_content:
                                    content = message.server_content
                                    if content.model_turn:
                                        for part in content.model_turn.parts:
                                            if part.inline_data:
                                                try:
                                                    await websocket.send_bytes(
                                                        part.inline_data.data
                                                    )
                                                except Exception:
                                                    break
                                            if part.text:
                                                print(
                                                    f"[COACH]: {part.text[:100]}"
                                                )

                                    if content.turn_complete:
                                        print("[SERVER] Turn complete.")
                                    if content.interrupted:
                                        print("[SERVER] Turn interrupted.")
                                        try:
                                            await websocket.send_json({"type": "interrupted"})
                                        except Exception:
                                            break

                                if message.usage_metadata:
                                    print("[SERVER] Usage metadata received.")

                            # receive() iterator exhausted (turn done) — loop
                            print("[SERVER] Ready for next turn.")

                    except Exception as e:
                        print(f"[SERVER] Gemini Receiver Error: {e}")
                        traceback.print_exc()

                # --- Client → Queue -----------------------------------------
                input_queue: asyncio.Queue = asyncio.Queue()

                async def websocket_receiver():
                    """Drain the client WebSocket into an async queue."""
                    try:
                        while True:
                            data = await websocket.receive()
                            await input_queue.put(data)
                    except Exception:
                        pass

                # --- Queue → Gemini -----------------------------------------
                async def queue_processor():
                    """Process queued messages and forward to Gemini.

                    Audio blobs go via ``send_realtime_input`` (with
                    automatic VAD for turn-end detection).
                    Text queries go via ``send_client_content``.
                    """
                    try:
                        while True:
                            data = await input_queue.get()

                            if "bytes" in data:
                                # Audio chunk — stream as realtime input
                                await session.send_realtime_input(
                                    media=types.Blob(
                                        data=data["bytes"],
                                        mime_type="audio/pcm;rate=16000",
                                    )
                                )

                            elif "text" in data:
                                msg = json.loads(data["text"])
                                t = msg.get("type")

                                if t == "text_query":
                                    query = msg.get("text", "")
                                    print(
                                        f"[SERVER] Text query: {query}"
                                    )
                                    await session.send_client_content(
                                        turns=types.Content(
                                            role="user",
                                            parts=[types.Part(text=query)],
                                        ),
                                        turn_complete=True,
                                    )

                            input_queue.task_done()
                    except Exception as e:
                        print(f"[SERVER] Processor Error: {e}")
                        traceback.print_exc()

                await asyncio.gather(
                    gemini_to_client(),
                    websocket_receiver(),
                    queue_processor(),
                )

        except Exception as e:
            print(f"[SERVER] FATAL: {e}")
            traceback.print_exc()
        finally:
            print("[SERVER] Closing Session.")
            try:
                await websocket.close()
            except Exception:
                pass


voice_handler = VoiceHandler()
