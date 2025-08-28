#!/usr/bin/env python3
"""
Working test script for Gemini API
"""

import os
from google.oauth2 import service_account
import google.generativeai as genai

def test_gemini_working():
    """Test Gemini API with correct configuration"""
    
    print("🧪 Working Gemini API Test")
    print("=" * 40)
    
    # Check service account file
    service_account_path = "keys/static-manifest-470317-t1-8f7c6a83cfb5.json"
    if not os.path.exists(service_account_path):
        print(f"❌ Service account file not found: {service_account_path}")
        return False
    
    print(f"✅ Service account file found: {service_account_path}")
    
    try:
        # Load credentials
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        print("✅ Credentials loaded successfully")
        
        # Configure Google AI
        genai.configure(credentials=credentials)
        print("✅ Google AI configured successfully")
        
        # Test the model
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Model created successfully")
        
        # Test a simple response
        response = model.generate_content("Hello! Say hi back.")
        print(f"✅ Response received: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_gemini_working()
