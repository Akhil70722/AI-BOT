import os
import asyncio
import csv
import json
import base64
import tempfile
import wave
import io
from datetime import datetime
import uuid

import websockets
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import speech_recognition as sr
import pyttsx3
import threading
import queue
from pydub import AudioSegment
import time

# Try different import approaches for Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    USE_GOOGLE_AI = True
except ImportError:
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        GEMINI_AVAILABLE = True
        USE_VERTEX_AI = True
        USE_GOOGLE_AI = False
    except ImportError:
        GEMINI_AVAILABLE = False
        USE_VERTEX_AI = False
        USE_GOOGLE_AI = False

load_dotenv = True
# ---------- CONFIG ----------
PORT = 8765
LOG_FILE = "chat_log.csv"
AUDIO_LOG_DIR = "audio_logs"
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')  # Your API key from Google AI Studio
# Prefer faster Flash model; will fall back if unavailable
PREFERRED_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]
# Toggle to disable TTS for faster responses
ENABLE_TTS = True
# ----------------------------

# Create audio logs directory
if not os.path.exists(AUDIO_LOG_DIR):
    os.makedirs(AUDIO_LOG_DIR)

# Initialize Speech Recognition
def initialize_speech_recognition():
    """Initialize speech recognition"""
    try:
        recognizer = sr.Recognizer()
        print("Speech recognition initialized successfully")
        return recognizer
    except Exception as e:
        print(f"Error initializing speech recognition: {e}")
        return None

# Initialize TTS engine
def initialize_tts():
    """Initialize text-to-speech engine"""
    try:
        engine = pyttsx3.init()
        # Configure TTS settings
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
        
        # Get available voices and set a good one
        voices = engine.getProperty('voices')
        if voices:
            # Try to find a female voice, otherwise use the first available
            for voice in voices:
                if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                    engine.setProperty('voice', voice.id)
                    break
            else:
                engine.setProperty('voice', voices[0].id)
        
        print("TTS engine initialized successfully")
        return engine
    except Exception as e:
        print(f"Error initializing TTS engine: {e}")
        return None

class GeminiClient:
    """Async wrapper for Gemini text generation with lazy initialization."""
    def __init__(self, api_key: str, preferred_models: list, max_tokens: int = 128, temperature: float = 0.7):
        self.api_key = api_key
        self.preferred_models = preferred_models
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.model = None
        self.initialized = False

    def _init_blocking(self):
        genai.configure(api_key=self.api_key)
        last_error = None
        for name in self.preferred_models:
            try:
                self.model = genai.GenerativeModel(name)
                self.initialized = True
                print(f"Using Gemini model: {name}")
                return True
            except Exception as e:
                last_error = e
                continue
        if last_error:
            raise last_error
        return False

    async def ensure_initialized(self) -> bool:
        if self.initialized and self.model is not None:
            return True
        try:
            return await asyncio.to_thread(self._init_blocking)
        except Exception as e:
            print(f"Error initializing Gemini: {e}")
            self.initialized = False
            self.model = None
            return False

    async def generate(self, prompt: str) -> str:
        ok = await self.ensure_initialized()
        if not ok:
            return "Error: Gemini model not initialized. Please check your API key configuration."
        def _gen():
            cfg = {
                "candidate_count": 1,
                "max_output_tokens": self.max_tokens,
                "temperature": self.temperature,
                "top_p": 0.95,
            }
            resp = self.model.generate_content(prompt, generation_config=cfg)
            # Robust text extraction: support multi-part responses
            def extract_text(r) -> str:
                # 1) Simple accessor
                t = getattr(r, 'text', None)
                if isinstance(t, str) and t.strip():
                    return t
                # 2) Top-level parts (some SDK versions expose .parts)
                parts = getattr(r, 'parts', None)
                if parts:
                    buf = []
                    for p in parts:
                        v = getattr(p, 'text', None)
                        if isinstance(v, str):
                            buf.append(v)
                    if buf:
                        return "".join(buf)
                # 3) Candidates -> content.parts
                candidates = getattr(r, 'candidates', None)
                if candidates:
                    for cand in candidates:
                        content = getattr(cand, 'content', None)
                        if not content:
                            continue
                        cparts = getattr(content, 'parts', None)
                        if not cparts:
                            continue
                        buf = []
                        for p in cparts:
                            v = getattr(p, 'text', None)
                            if isinstance(v, str):
                                buf.append(v)
                        if buf:
                            return "".join(buf)
                return ""
            text = extract_text(resp)
            return text if text else ""
        try:
            return await asyncio.wait_for(asyncio.to_thread(_gen), timeout=4.0)
        except asyncio.TimeoutError:
            return "I'm still thinking; here is a brief answer while I finish processing."
        except Exception as e:
            return f"Error generating response: {e}"

# Initialize all models
speech_recognizer = initialize_speech_recognition()
tts_engine = initialize_tts()
gemini_client = GeminiClient(GEMINI_API_KEY, PREFERRED_GEMINI_MODELS, max_tokens=128, temperature=0.7)

# Audio processing functions
def process_audio_data(audio_base64, session_id):
    """Convert base64 audio data to text using Google Speech Recognition, fully in-memory to avoid file locks."""
    try:
        # Decode base64 audio data
        audio_bytes = base64.b64decode(audio_base64)

        # Save original user audio bytes for logging (as .wav even if container differs)
        try:
            audio_filename = f"{AUDIO_LOG_DIR}/user_audio_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            with open(audio_filename, 'wb') as audio_file:
                audio_file.write(audio_bytes)
        except Exception as e:
            print(f"Warning: could not write user audio log: {e}")

        # Attempt to open as WAV directly (guard against missing file/ffmpeg issues)
        pcm_bytes: bytes
        try:
            with wave.open(io.BytesIO(audio_bytes), 'rb') as wf:
                pcm_bytes = audio_bytes
        except Exception:
            try:
                # Prefer pydub if ffmpeg available; otherwise raise a clear error
                sound = AudioSegment.from_file(io.BytesIO(audio_bytes))
                buf = io.BytesIO()
                sound.export(buf, format='wav')
                pcm_bytes = buf.getvalue()
            except FileNotFoundError as e:
                return "Error processing audio: ffmpeg or codecs not found. Please install ffmpeg and restart."
            except Exception as e:
                return f"Error processing audio: {e}"

        # SpeechRecognition from memory
        if not speech_recognizer:
            return "Error: Speech recognition not available"

        with sr.AudioFile(io.BytesIO(pcm_bytes)) as source:
            audio = speech_recognizer.record(source)
            transcribed_text = speech_recognizer.recognize_google(audio)
            print(f"Transcribed: {transcribed_text}")
            return transcribed_text

    except Exception as e:
        print(f"Error processing audio: {e}")
        return f"Error processing audio: {e}"

def text_to_speech(text, session_id):
    """Convert text to speech and return as base64 audio data"""
    try:
        if not tts_engine:
            return None, "Error: TTS engine not available"
        
        # Create a temporary file for the audio output
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # Generate speech
            tts_engine.save_to_file(text, temp_file_path)
            tts_engine.runAndWait()
            
            # Read the generated audio file with retries (Windows can briefly lock the file)
            audio_data = None
            for _ in range(10):
                try:
                    with open(temp_file_path, 'rb') as audio_file:
                        audio_data = audio_file.read()
                    break
                except PermissionError:
                    time.sleep(0.1)
                except Exception as e:
                    raise e
            if audio_data is None:
                return None, "Error: Could not read generated TTS file"
            
            # Save the audio file for logging
            audio_filename = f"{AUDIO_LOG_DIR}/bot_audio_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            try:
                with open(audio_filename, 'wb') as audio_file:
                    audio_file.write(audio_data)
            except Exception as e:
                print(f"Warning: could not save bot audio log: {e}")
            
            # Convert to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            return audio_base64, None
            
        finally:
            # Clean up temporary file with retries
            for _ in range(10):
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                    break
                except PermissionError:
                    time.sleep(0.1)
                except Exception:
                    break
                
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        return None, f"Error in text-to-speech: {e}"

# Ensure CSV has header (create if missing or wrong format)
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_iso", "session_id", "user_message", "bot_response", "user_audio_file", "bot_audio_file"])
else:
    try:
        with open(LOG_FILE, encoding='utf-8') as f:
            first_line = f.readline()
        expected_header = ",".join(["timestamp_iso", "session_id", "user_message", "bot_response", "user_audio_file", "bot_audio_file"]) + "\n"
        if first_line != expected_header:
            backup_path = LOG_FILE + ".backup"
            try:
                os.replace(LOG_FILE, backup_path)
                with open(LOG_FILE, mode="w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["timestamp_iso", "session_id", "user_message", "bot_response", "user_audio_file", "bot_audio_file"])
                print(f"Backed up legacy log format to {backup_path} and wrote new header.")
            except Exception as e:
                print(f"Warning: could not backup/initialize new CSV header: {e}")
    except Exception as e:
        print(f"Warning: could not validate CSV header: {e}")

async def handle_connection(websocket):
    """Handle WebSocket connections and chat messages"""
    # Generate unique session ID for this connection
    session_id = str(uuid.uuid4())[:8]
    print(f"New connection with session ID: {session_id}")
    # Send session immediately so frontend updates without waiting for first response
    try:
        await websocket.send(json.dumps({
            "type": "session",
            "session_id": session_id,
            "content": ""
        }))
    except Exception:
        pass
    
    async for message in websocket:
        try:
            # Parse the message
            if isinstance(message, str):
                # Handle text message
                user_msg = message.strip()
                if not user_msg:
                    await websocket.send(json.dumps({
                        "type": "text",
                        "content": "Please send a non-empty message."
                    }))
                    continue
                
                # Process text message
                await process_text_message(websocket, user_msg, session_id)
                
            else:
                # Handle binary audio message
                await process_audio_message(websocket, message, session_id)
                
        except Exception as e:
            error_response = f"Error processing message: {e}"
            print(f"Error in handle_connection: {e}")
            await websocket.send(json.dumps({
                "type": "text",
                "content": error_response
            }))

async def process_text_message(websocket, user_msg, session_id):
    """Process text message and generate response"""
    try:
        bot_text = await gemini_client.generate(user_msg)
        bot_text = bot_text.strip() if isinstance(bot_text, str) else str(bot_text)
        if not bot_text:
            bot_text = "I couldn't generate a response. Please try again."

        if not bot_text:
            bot_text = "I couldn't generate a response. Please try again."

        # Convert text response to speech in a background thread (blocking)
        audio_base64, tts_error = (None, None)
        if ENABLE_TTS:
            audio_base64, tts_error = await asyncio.to_thread(text_to_speech, bot_text, session_id)
        
        # Get audio filenames for logging
        user_audio_file = "N/A"  # Text input, no audio
        bot_audio_file = f"bot_audio_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav" if audio_base64 else "N/A"
        
        # Log to CSV in background so response can be sent immediately
        def _log_row():
            try:
                with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([datetime.now().isoformat(), session_id, user_msg, bot_text, user_audio_file, bot_audio_file])
                    f.flush()
                    try:
                        os.fsync(f.fileno())
                    except Exception:
                        pass
            except Exception as e:
                print(f"Error logging to CSV: {e}")
        asyncio.create_task(asyncio.to_thread(_log_row))

        # Send response back to browser
        response_data = {
            "type": "text",
            "content": bot_text,
            "session_id": session_id
        }
        
        if audio_base64:
            response_data["audio"] = audio_base64
        elif tts_error:
            response_data["tts_error"] = tts_error
            
        await websocket.send(json.dumps(response_data))
        
    except Exception as e:
        bot_text = f"Error generating response: {e}"
        await websocket.send(json.dumps({
            "type": "text",
            "content": bot_text
        }))

async def process_audio_message(websocket, audio_data, session_id):
    """Process audio message and generate response"""
    try:
        # Convert audio to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Transcribe audio to text off the event loop (blocking I/O + CPU)
        transcribed_text = await asyncio.to_thread(process_audio_data, audio_base64, session_id)
        
        if isinstance(transcribed_text, str) and transcribed_text.startswith("Error"):
            # Log the failed audio attempt as a row so history shows the issue
            def _log_error_row():
                try:
                    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
                        writer = csv.writer(f)
                        writer.writerow([datetime.now().isoformat(), session_id, "[voice message]", transcribed_text, f"user_audio_{session_id}.wav", "N/A"])
                except Exception as e:
                    print(f"Error logging audio error to CSV: {e}")
            asyncio.create_task(asyncio.to_thread(_log_error_row))

            await websocket.send(json.dumps({
                "type": "text",
                "content": transcribed_text
            }))
            return
        
        # Process the transcribed text
        await process_text_message(websocket, transcribed_text, session_id)
        
    except Exception as e:
        error_response = f"Error processing audio: {e}"
        await websocket.send(json.dumps({
            "type": "text",
            "content": error_response
        }))

async def main():
    """Main function to start the WebSocket server"""
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY missing.")
    
    if speech_recognizer is None:
        print("Warning: Speech recognition not initialized. Speech-to-text will not work.")
    
    if tts_engine is None:
        print("Warning: TTS engine not initialized. Text-to-speech will not work.")
    
    # Increase max_size to support voice blobs and set robust ping settings
    async with websockets.serve(
        handle_connection,
        "127.0.0.1",
        PORT,
        max_size=20 * 1024 * 1024,  # 20 MB
        ping_interval=20,
        ping_timeout=20,
    ):
        print(f"WebSocket server running at ws://127.0.0.1:{PORT}")
        print(f"Chat logs will be saved to: {LOG_FILE}")
        print(f"Audio logs will be saved to: {AUDIO_LOG_DIR}/")
        print("Voice features enabled: Speech-to-Text and Text-to-Speech")
        print(f"Using Gemini API key: {GEMINI_API_KEY[:10]}...")
        await asyncio.Future()  # run forever


# --- HTTP Server for chat history ---
class ChatLogHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/chat_history':
            try:
                with open(LOG_FILE, encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    history = list(reader)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(history).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def start_http_server():
    httpd = HTTPServer(('127.0.0.1', 8080), ChatLogHandler)
    print('HTTP server running at http://127.0.0.1:8080/chat_history')
    httpd.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=start_http_server, daemon=True).start()
    asyncio.run(main())
