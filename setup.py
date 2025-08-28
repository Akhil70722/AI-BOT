#!/usr/bin/env python3
"""
Setup script for AI Voicebot WebSocket Chatbot
This script helps configure the GCP project ID in the necessary files.
"""

import os
import re

def update_project_id_in_file(file_path, old_project_id, new_project_id):
    """Update project ID in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the project ID
        updated_content = content.replace(old_project_id, new_project_id)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        return True
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    print("🚀 AI Voicebot Setup Script")
    print("=" * 40)
    
    # Check if service account key exists
    if not os.path.exists("keys/static-manifest-470317-t1-8f7c6a83cfb5.json"):
        print("❌ Service account key not found!")
        print("Please place your GCP service account JSON key in the 'keys/static-manifest-470317-t1-8f7c6a83cfb5.json' file")
        return
    
    # Get current project ID from files
    current_project_id = "your-project-id"
    
    print(f"Current project ID: {current_project_id}")
    print()
    
    # Ask for new project ID
    new_project_id = input("Enter your GCP Project ID: ").strip()
    
    if not new_project_id:
        print("❌ Project ID cannot be empty!")
        return
    
    if new_project_id == current_project_id:
        print("✅ Project ID is already set correctly!")
        return
    
    # Files to update
    files_to_update = [
        ("server.py", current_project_id, new_project_id),
        ("test_gemini.py", current_project_id, new_project_id)
    ]
    
    print(f"\n📝 Updating project ID to: {new_project_id}")
    
    success_count = 0
    for file_path, old_id, new_id in files_to_update:
        if update_project_id_in_file(file_path, old_id, new_id):
            print(f"✅ Updated {file_path}")
            success_count += 1
        else:
            print(f"❌ Failed to update {file_path}")
    
    print(f"\n🎉 Setup complete! Updated {success_count}/{len(files_to_update)} files.")
    print("\nNext steps:")
    print("1. Run: python test_gemini.py (to test your configuration)")
    print("2. Run: python server.py (to start the WebSocket server)")
    print("3. Open client.html in your browser")

if __name__ == "__main__":
    main()
