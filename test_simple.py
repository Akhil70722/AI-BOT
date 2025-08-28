#!/usr/bin/env python3
"""
Simple test script to verify text messages work without TTS
"""

import asyncio
import websockets
import json

async def test_simple_text():
    uri = "ws://127.0.0.1:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Wait for session message
            session_msg = await websocket.recv()
            print(f"📨 Session message: {session_msg}")
            
            # Send a simple text message (should not generate audio)
            test_message = "Hello, this is a simple test message"
            print(f"📤 Sending: {test_message}")
            await websocket.send(test_message)
            
            # Wait for response
            response = await websocket.recv()
            print(f"📨 Response received!")
            
            # Parse response to check if it has audio
            try:
                data = json.loads(response)
                if "audio" in data:
                    print(f"❌ Response still contains audio (length: {len(data['audio'])} chars)")
                else:
                    print(f"✅ Response is clean text: {data.get('content', 'No content')[:100]}...")
            except json.JSONDecodeError:
                print(f"❌ Response is not valid JSON: {response[:100]}...")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_text())
