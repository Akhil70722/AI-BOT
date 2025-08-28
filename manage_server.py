#!/usr/bin/env python3
"""
AI Voicebot Server Manager
Helps manage the server - check status, kill existing processes, start server
"""

import os
import sys
import subprocess
import signal
import time

def check_server_status():
    """Check if server is running on port 8765"""
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        if ':8765' in result.stdout:
            return True
        return False
    except:
        return False

def kill_server():
    """Kill any process using port 8765"""
    try:
        # Find process using port 8765
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if ':8765' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    print(f"Killing process {pid} using port 8765...")
                    subprocess.run(['taskkill', '/PID', pid, '/F'], check=True)
                    print("✅ Server stopped")
                    return True
        
        print("No server found running on port 8765")
        return False
    except Exception as e:
        print(f"Error killing server: {e}")
        return False

def start_server():
    """Start the server"""
    if check_server_status():
        print("⚠️  Server is already running on port 8765")
        response = input("Do you want to stop it and start a new one? (y/n): ")
        if response.lower() == 'y':
            kill_server()
        else:
            print("Server not started")
            return
    
    print("🚀 Starting AI Voicebot Server...")
    print("📝 Instructions:")
    print("   1. Server will be available at ws://127.0.0.1:8765")
    print("   2. Open client.html in your web browser")
    print("   3. You can type messages OR click the microphone to speak")
    print("   4. Press Ctrl+C to stop the server")
    print("\n" + "="*60)
    
    try:
        subprocess.run([sys.executable, 'server.py'])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")

def main():
    if len(sys.argv) < 2:
        print("AI Voicebot Server Manager")
        print("Usage:")
        print("  python manage_server.py start   - Start the server")
        print("  python manage_server.py stop    - Stop the server")
        print("  python manage_server.py status  - Check server status")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'start':
        start_server()
    elif command == 'stop':
        kill_server()
    elif command == 'status':
        if check_server_status():
            print("✅ Server is running on port 8765")
        else:
            print("❌ Server is not running")
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
