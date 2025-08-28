# AI Voicebot - WebSocket Chatbot with Gemini AI

A real-time WebSocket chatbot powered by Google's Gemini AI (Vertex AI) that allows users to chat through a web browser interface.

## Features

- 🤖 **Gemini AI Integration**: Powered by Google's Gemini 1.5 Flash model
- 🌐 **Real-time WebSocket Communication**: Instant message exchange
- 📝 **Chat Logging**: All conversations are logged to CSV file
- 🎨 **Modern UI**: Beautiful, responsive web interface
- 🔄 **Auto-reconnection**: Automatic reconnection on connection loss
- 📊 **Message History**: Persistent chat logs with timestamps

## Prerequisites

1. **Google Cloud Platform (GCP) Account**
   - Enable Vertex AI API
   - Create a service account with appropriate permissions
   - Download the service account key JSON file

2. **Python 3.8+**

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure GCP

1. **Enable APIs**: In your GCP Console, enable the following APIs:
   - Vertex AI API
   - Cloud AI Platform API

2. **Create Service Account**:
   - Go to IAM & Admin > Service Accounts
   - Create a new service account
   - Grant the following roles:
     - Vertex AI User
     - Vertex AI Service Agent
   - Create and download the JSON key file

3. **Update Configuration**:
   - Place your service account JSON file in the `keys/` directory
   - Update `GCP_PROJECT_ID` in `server.py` with your actual project ID

### 3. Update Server Configuration

**Option A: Use the setup script (Recommended)**
```bash
python setup.py
```
This will prompt you for your GCP project ID and automatically update all necessary files.

**Option B: Manual configuration**
Edit `server.py` and `test_gemini.py` and update these variables:

```python
GCP_PROJECT_ID = "your-actual-project-id"  # Replace with your GCP project ID
GCP_LOCATION = "us-central1"               # Your preferred region
SERVICE_ACCOUNT_PATH = "keys/gcp-sa.json"  # Path to your service account key
```

## Usage

### 1. Start the Server

```bash
python server.py
```

You should see:
```
WebSocket server running at ws://127.0.0.1:8765
Chat logs will be saved to: chat_log.csv
```

### 2. Open the Client

Open `client.html` in your web browser. You can:
- Double-click the file
- Or serve it using a local server: `python -m http.server 8000`

### 3. Start Chatting

- Type your message in the input field
- Press Enter or click Send
- The AI will respond using Gemini
- All conversations are automatically logged to `chat_log.csv`

## File Structure

```
AI Voicebot/
├── server.py              # WebSocket server with Gemini integration
├── client.html            # Web client interface
├── requirements.txt       # Python dependencies
├── chat_log.csv          # Chat conversation logs
├── keys/
│   └── gcp-sa.json       # GCP service account key
└── README.md             # This file
```

## Chat Log Format

The `chat_log.csv` file contains:
- `timestamp_iso`: ISO format timestamp
- `user_message`: User's input message
- `bot_response`: AI's response

## Troubleshooting

### Common Issues

1. **"Gemini model not initialized"**
   - Check your GCP project ID
   - Verify service account key is in the correct location
   - Ensure Vertex AI API is enabled

2. **"Connection refused"**
   - Make sure the server is running
   - Check if port 8765 is available
   - Verify firewall settings

3. **"Authentication error"**
   - Verify service account has correct permissions
   - Check if the JSON key file is valid
   - Ensure the project ID matches your GCP project

### Debug Mode

To see detailed error messages, check the server console output for any error messages.

## Security Notes

- Keep your service account key secure
- Don't commit the key file to version control
- Consider using environment variables for production

## Next Steps

This implementation covers Task 1. The system is ready for additional features like:
- Voice input/output
- Multi-user support
- Advanced conversation management
- Integration with other AI services

## License

This project is for educational purposes. Please ensure compliance with Google's API usage terms and conditions.
