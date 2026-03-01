"""Smoke test for Phase 2 text chat backend.

Asks the Wololo Coach 5 strategic questions to verify grounding and persona.
"""

import asyncio
import httpx
import json

QUESTIONS = [
    "What counters a Frank Paladin?",
    "I'm playing as Britons, what should my late-game army look like?",
    "Opponent is massing Mangonels, what is the best counter?",
    "How much does a Trebuchet cost?",
    "What are the strengths of the Japanese civilization?"
]

async def smoke_test():
    url = "http://localhost:8000/ask"
    print(f"--- Wololo Coach Smoke Test ---")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, q in enumerate(QUESTIONS, 1):
            print(f"\n[{i}] Question: {q}")
            try:
                response = await client.post(url, json={"query": q})
                if response.status_code == 200:
                    answer = response.json().get("answer", "")
                    print(f"Coach: {answer}")
                else:
                    print(f"Error {response.status_code}: {response.text}")
            except Exception as e:
                print(f"Connection Error: {e}. Is the server running? (uvicorn server.main:app)")
                break

if __name__ == "__main__":
    # Note: This requires the server to be running in another terminal
    # uvicorn server.main:app --port 8000
    try:
        asyncio.run(smoke_test())
    except KeyboardInterrupt:
        pass
