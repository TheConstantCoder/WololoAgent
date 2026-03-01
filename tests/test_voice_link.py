# tests/test_voice_link.py
import asyncio
import websockets
import json

async def test_voice_link():
    uri = "ws://127.0.0.1:8000/voice"
    print(f"Connecting to {uri}...")
    try:
        async with websockets.connect(uri) as ws:
            print("Connected! Sending 'end_of_turn' trigger...")
            # Send a trigger to get Gemini to say something
            await ws.send(json.dumps({"type": "end_of_turn"})) 
            
            print("Waiting for response...")
            # Wait for any response
            msg = await asyncio.wait_for(ws.recv(), timeout=15.0)
            if isinstance(msg, bytes):
                print(f"Success! Received {len(msg)} bytes of audio data from Gemini.")
            else:
                print(f"Received control message: {msg}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_voice_link())
