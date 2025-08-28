#!/usr/bin/env python3
"""
Diagnostic script to identify and fix common issues with the AI Voicebot
"""

import os
import json
import subprocess
import sys

def check_gemini_api_key():
    """Check if Gemini API key is configured"""
    print("🔍 Checking Gemini API Key...")
    
    # Check if API key is in server.py
    try:
        with open("server.py", 'r') as f:
            content = f.read()
            if "AIzaSyAnYG9ri4f9MHtNhnCVXjmBHBEvXwREhZE" in content:
                print("✅ Gemini API key found in server.py")
                return True
            else:
                print("❌ Gemini API key not found in server.py")
                return False
    except Exception as e:
        print(f"❌ Error reading server.py: {e}")
        return False

def check_whisper_cache():
    """Check if Whisper model cache exists"""
    print("\n🔍 Checking Whisper Model Cache...")
    
    # Check for .cache directory
    cache_dir = ".cache"
    whisper_cache = os.path.join(cache_dir, "whisper")
    
    if not os.path.exists(cache_dir):
        print(f"❌ Cache directory not found: {cache_dir}")
        print("   Creating cache directory...")
        try:
            os.makedirs(cache_dir)
            print("✅ Cache directory created")
        except Exception as e:
            print(f"❌ Failed to create cache directory: {e}")
            return False
    
    if not os.path.exists(whisper_cache):
        print(f"❌ Whisper cache directory not found: {whisper_cache}")
        print("   Creating Whisper cache directory...")
        try:
            os.makedirs(whisper_cache)
            print("✅ Whisper cache directory created")
        except Exception as e:
            print(f"❌ Failed to create Whisper cache directory: {e}")
            return False
    
    # Check if any Whisper models exist
    model_files = []
    if os.path.exists(whisper_cache):
        for file in os.listdir(whisper_cache):
            if file.endswith('.pt') or file.endswith('.bin'):
                model_files.append(file)
    
    if model_files:
        print(f"✅ Found {len(model_files)} Whisper model files:")
        for file in model_files:
            print(f"   - {file}")
    else:
        print("⚠️  No Whisper model files found")
        print("   The first voice message will download the model automatically")
    
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    print("\n🔍 Checking Python Dependencies...")
    
    required_packages = [
        'whisper',
        'pyttsx3',
        'google.generativeai',
        'websockets'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'whisper':
                import whisper
            elif package == 'pyttsx3':
                import pyttsx3
            elif package == 'google.generativeai':
                import google.generativeai
            elif package == 'websockets':
                import websockets
            
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("   Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def test_gemini_connection():
    """Test Gemini API connection"""
    print("\n🔍 Testing Gemini API Connection...")
    
    try:
        import google.generativeai as genai
        
        # Configure with API key
        api_key = "AIzaSyAnYG9ri4f9MHtNhnCVXjmBHBEvXwREhZE"
        genai.configure(api_key=api_key)
        
        # Test with a simple request
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello")
        
        if response.text:
            print("✅ Gemini API connection successful")
            return True
        else:
            print("❌ Gemini API returned empty response")
            return False
            
    except Exception as e:
        print(f"❌ Gemini API connection failed: {e}")
        return False

def provide_solutions():
    """Provide solutions for common issues"""
    print("\n" + "="*60)
    print("🔧 SOLUTIONS FOR COMMON ISSUES")
    print("="*60)
    
    print("\n1. Gemini API Key Issues:")
    print("   - Verify your API key is valid at: https://aistudio.google.com/app/apikey")
    print("   - Check if the API key has proper permissions")
    print("   - Ensure you have quota available")
    print("   - Try regenerating the API key if needed")
    
    print("\n2. Whisper Model Issues:")
    print("   - The first voice message will automatically download the model")
    print("   - Ensure you have internet connection for the first download")
    print("   - Check disk space (models are ~1GB)")
    print("   - If download fails, try: pip install --upgrade openai-whisper")
    
    print("\n3. Missing Dependencies:")
    print("   - Activate your virtual environment: venv\\Scripts\\Activate.ps1")
    print("   - Install missing packages: pip install -r requirements.txt")
    
    print("\n4. Quick Fix Commands:")
    print("   # Activate virtual environment")
    print("   venv\\Scripts\\Activate.ps1")
    print("   ")
    print("   # Install dependencies")
    print("   pip install -r requirements.txt")
    print("   ")
    print("   # Test voice components")
    print("   python test_voice.py")
    print("   ")
    print("   # Start server")
    print("   python server.py")

def main():
    """Run all diagnostics"""
    print("="*60)
    print("🔍 AI Voicebot Diagnostic Tool")
    print("="*60)
    
    # Run all checks
    api_key_ok = check_gemini_api_key()
    whisper_ok = check_whisper_cache()
    deps_ok = check_dependencies()
    
    # Only test Gemini if API key is configured
    gemini_ok = False
    if api_key_ok:
        gemini_ok = test_gemini_connection()
    
    # Summary
    print("\n" + "="*60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*60)
    
    print(f"Gemini API Key: {'✅ OK' if api_key_ok else '❌ ISSUE'}")
    print(f"Whisper Cache:  {'✅ OK' if whisper_ok else '❌ ISSUE'}")
    print(f"Dependencies:   {'✅ OK' if deps_ok else '❌ ISSUE'}")
    print(f"Gemini API:     {'✅ OK' if gemini_ok else '❌ ISSUE'}")
    
    if all([api_key_ok, whisper_ok, deps_ok, gemini_ok]):
        print("\n🎉 All systems are working! You can start the server.")
        print("Run: python server.py")
    else:
        print("\n⚠️  Some issues were found. Check the solutions below.")
        provide_solutions()

if __name__ == "__main__":
    main()
