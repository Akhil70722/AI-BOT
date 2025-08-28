#!/usr/bin/env python3
"""
Configuration script for AI Voicebot
This script helps set up the Gemini API key and other configuration.
"""

import os
import sys

def create_env_file():
    """Create or update .env file with API key"""
    env_file = ".env"
    
    # Check if .env already exists
    if os.path.exists(env_file):
        print("⚠️  .env file already exists!")
        overwrite = input("Do you want to overwrite it? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Configuration cancelled.")
            return False
    
    print("\n🔑 Gemini API Key Setup")
    print("=" * 40)
    print("1. Go to: https://makersuite.google.com/app/apikey")
    print("2. Sign in with your Google account")
    print("3. Click 'Create API Key'")
    print("4. Copy the generated API key")
    print()
    
    api_key = input("Enter your Gemini API key: ").strip()
    
    if not api_key:
        print("❌ API key cannot be empty!")
        return False
    
    # Create .env file content
    env_content = f"""# Gemini API Configuration
# Get your API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY={api_key}

# Server Configuration
HTTP_PORT=8081
WS_PORT=8765
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Created {env_file} with your API key")
        return True
    except Exception as e:
        print(f"❌ Error creating {env_file}: {e}")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    print("\n📦 Checking Dependencies")
    print("=" * 40)
    
    required_packages = [
        'google.generativeai',
        'speech_recognition',
        'pyttsx3',
        'websockets',
        'pydub'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'google.generativeai':
                import google.generativeai
            elif package == 'speech_recognition':
                import speech_recognition
            elif package == 'pyttsx3':
                import pyttsx3
            elif package == 'websockets':
                import websockets
            elif package == 'pydub':
                import pydub
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All required packages are installed!")
    return True

def main():
    print("🚀 AI Voicebot Configuration")
    print("=" * 40)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first.")
        return
    
    # Create .env file
    if create_env_file():
        print("\n🎉 Configuration complete!")
        print("\nNext steps:")
        print("1. Run: python server.py")
        print("2. Open client.html in your browser")
        print("3. Start chatting with your AI bot!")
    else:
        print("\n❌ Configuration failed. Please try again.")

if __name__ == "__main__":
    main()
