#!/usr/bin/env python3
"""
Simple WebSocket test client to debug communication issues
"""

import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://127.0.0.1:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket server")
            
            # Wait for session message
            session_msg = await websocket.recv()
            print(f"📨 Session message: {session_msg}")
            
            # Send a test message
            test_message = "Hello, this is a test message"
            print(f"📤 Sending: {test_message}")
            await websocket.send(test_message)
            
            # Wait for response
            response = await websocket.recv()
            print(f"📨 Response: {response}")
            
            # Try to parse the response
            try:
                parsed = json.loads(response)
                print(f"🔍 Parsed response: {json.dumps(parsed, indent=2)}")
                
                if 'content' in parsed:
                    print(f"✅ Content found: {parsed['content']}")
                else:
                    print("❌ No 'content' field in response")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse response as JSON: {e}")
                print(f"Raw response: {response}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing WebSocket communication...")
    asyncio.run(test_websocket())
