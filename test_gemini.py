import os
from google.cloud import aiplatform
from google.oauth2 import service_account


def test_gemini_connection():
    """Test Gemini API connection with Vertex AI using service account JSON."""

    # ✅ Path to your downloaded service account key
    SERVICE_ACCOUNT_PATH = "keys/static-manifest-470317-t1-8f7c6a83cfb5.json"

    # ✅ Replace with your actual project details
    PROJECT_ID = "static-manifest-470317-t1"  # Your GCP project ID
    LOCATION = "us-central1"  # Gemini is available here

    try:
        # Check if service account file exists
        if not os.path.exists(SERVICE_ACCOUNT_PATH):
            print(f"❌ Error: Service account file not found at {SERVICE_ACCOUNT_PATH}")
            return False

        # ✅ Load service account credentials properly
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_PATH
        )

        # Init Vertex AI with service account
        aiplatform.init(
            project=PROJECT_ID,
            location=LOCATION,
            credentials=credentials,
        )

        # Import Vertex AI Generative Model
        from vertexai.generative_models import GenerativeModel

        # Load Gemini model
        model = GenerativeModel("gemini-1.5-flash")

        # Test prompts
        test_messages = [
            "Hello! Can you introduce yourself?",
            "What's 2 + 2?",
            "Tell me a short joke"
        ]

        print("🤖 Testing Gemini API Connection...")
        print("=" * 50)

        for i, message in enumerate(test_messages, 1):
            print(f"\n📝 Test {i}: {message}")
            print("-" * 30)

            response = model.generate_content(message)
            print(f"🤖 Response: {response.text.strip() if response.text else '⚠️ Empty response'}")

        print("\n" + "=" * 50)
        print("✅ Gemini API test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error testing Gemini API: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Ensure Vertex AI API is enabled in your GCP project")
        print("2. Verify your service account has the correct roles (Vertex AI User)")
        print("3. Check that your service account key file is valid JSON")
        return False


if __name__ == "__main__":
    print("🧪 Gemini API Test Script")
    print("This script tests your Gemini API configuration before running the main server.\n")
    test_gemini_connection()
