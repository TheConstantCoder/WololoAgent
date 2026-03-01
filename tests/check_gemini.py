import asyncio
import os
from google import genai
from google.genai import types
from server.config import settings

async def check_gemini():
    model_id = settings.gemini_model
    print(f"Testing Gemini Live API with model: {model_id}")
    
    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(api_version='v1alpha')
    )
    
    config = {
        'response_modalities': ['AUDIO']
    }
    
    try:
        async with client.aio.live.connect(model=model_id, config=config) as session:
            print("Successfully connected to Gemini Live API!")
            # Correct call for AsyncSession.send
            await session.send(input="Hello", end_of_turn=True)
            async for message in session.receive():
                if message.server_content:
                    print("Received response from Gemini")
                    break
    except Exception as e:
        print(f"Failed to connect to Gemini: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_gemini())
