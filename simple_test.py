#!/usr/bin/env python3
"""
Simple test script to check Gemini API connectivity
"""

import os
from google.oauth2 import service_account

def test_gemini_simple():
    """Simple test to check if we can connect to Gemini API"""
    
    print("🧪 Simple Gemini API Test")
    print("=" * 40)
    
    # Check service account file
    service_account_path = "keys/static-manifest-470317-t1-8f7c6a83cfb5.json"
    if not os.path.exists(service_account_path):
        print(f"❌ Service account file not found: {service_account_path}")
        return False
    
    print(f"✅ Service account file found: {service_account_path}")
    
    # Try to load credentials
    try:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        print("✅ Credentials loaded successfully")
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return False
    
    # Try different Gemini libraries
    libraries_to_try = [
        ("google.generativeai", "Google AI SDK"),
        ("vertexai", "Vertex AI SDK")
    ]
    
    for lib_name, lib_desc in libraries_to_try:
        print(f"\n🔍 Trying {lib_desc}...")
        try:
            if lib_name == "google.generativeai":
                import google.generativeai as genai
                genai.configure(credentials=credentials, project="coral-core-433614-s0")
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content("Hello! Say hi back.")
                print(f"✅ {lib_desc} works! Response: {response.text}")
                return True
                
            elif lib_name == "vertexai":
                import vertexai
                from vertexai.generative_models import GenerativeModel
                vertexai.init(project="coral-core-433614-s0", location="us-central1", credentials=credentials)
                model = GenerativeModel("gemini-1.5-flash")
                response = model.generate_content("Hello! Say hi back.")
                print(f"✅ {lib_desc} works! Response: {response.text}")
                return True
                
        except ImportError:
            print(f"❌ {lib_desc} not installed")
        except Exception as e:
            print(f"❌ {lib_desc} error: {e}")
    
    print("\n❌ No working Gemini library found")
    print("💡 Try installing: pip install google-generativeai")
    return False

if __name__ == "__main__":
    test_gemini_simple()
