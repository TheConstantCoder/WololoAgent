# tests/test_voice_link.py
"""Multi-turn smoke test for the Wololo Coach voice bridge.

Connects to the server, sends two sequential text queries,
and verifies both produce audio responses.

Usage:
    1. Start the server: uvicorn server.main:app --port 8000
    2. Run:  PYTHONUNBUFFERED=1 python tests/test_voice_link.py
"""

import asyncio
import json
import sys


async def main():
    import websockets
    uri = "ws://127.0.0.1:8000/voice"
    print(f"Connecting to {uri}...", flush=True)

    async with websockets.connect(uri, ping_interval=None) as ws:
        # Turn 1: send a text query
        q1 = "Hello coach, say wololo!"
        print(f"Sending Turn 1: {q1}", flush=True)
        await ws.send(json.dumps({"type": "text_query", "text": q1}))

        t1 = 0
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=15.0)
            except asyncio.TimeoutError:
                break
            if isinstance(msg, bytes):
                t1 += len(msg)
            else:
                print(f"  ctrl: {msg[:120]}", flush=True)
        print(f"Turn 1: {t1} bytes {'OK' if t1 else 'FAIL'}", flush=True)

        if not t1:
            sys.exit(1)

        # Turn 2: follow-up
        q2 = "Who are the Britons?"
        print(f"Sending Turn 2: {q2}", flush=True)
        await ws.send(json.dumps({"type": "text_query", "text": q2}))

        t2 = 0
        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=15.0)
            except asyncio.TimeoutError:
                break
            if isinstance(msg, bytes):
                t2 += len(msg)
            else:
                print(f"  ctrl: {msg[:120]}", flush=True)
        print(f"Turn 2: {t2} bytes {'OK' if t2 else 'FAIL'}", flush=True)

        if t1 and t2:
            print("MULTI-TURN SUCCESS!", flush=True)
        else:
            print("MULTI-TURN FAILED", flush=True)
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
