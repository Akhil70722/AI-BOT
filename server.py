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
    from google import genai
    GEMINI_AVAILABLE = True
    USE_GOOGLE_AI = True
    USE_VERTEX_AI = False
except ImportError:
    try:
        import google.generativeai as genai
        GEMINI_AVAILABLE = True
        USE_GOOGLE_AI = True
        USE_VERTEX_AI = False
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

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
# TTS model for voice integration
TTS_MODEL = "gemini-2.5-flash-preview-tts"
# Toggle to enable TTS for voice responses only
ENABLE_TTS_FOR_VOICE = True  # Enable TTS only for voice input responses
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
        try:
            # Try new google.genai library first
            if hasattr(genai, 'Client'):
                # New API
                self.client = genai.Client(api_key=self.api_key)
                self.model = None  # Not needed for new API
                self.initialized = True
                print(f"Using new Google GenAI API")
                return True
            else:
                # Fallback to old API
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
        except Exception as e:
            print(f"Error initializing Gemini: {e}")
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
            try:
                # Try new API first
                if hasattr(self, 'client'):
                    try:
                        print(f"Calling new Google GenAI API with prompt: {prompt[:100]}...")
                        # Try different model names in order of preference
                        models_to_try = [
                            "gemini-2.5-flash",
                            "gemini-2.0-flash-exp",
                            "gemini-2.0-flash",
                            "gemini-1.5-flash"
                        ]
                        
                        last_error = None
                        resp = None
                        for model_name in models_to_try:
                            try:
                                print(f"Trying model: {model_name}")
                                resp = self.client.models.generate_content(
                                    model=model_name,
                                    contents=prompt
                                )
                                print(f"Successfully used model: {model_name}")
                                break
                            except Exception as e:
                                print(f"Failed with model {model_name}: {e}")
                                last_error = e
                                continue
                        else:
                            # If all models failed
                            raise last_error or Exception("All models failed")
                        
                        print(f"API response received: {type(resp)}")
                        print(f"Response attributes: {dir(resp)}")
                        # New API has simple .text accessor
                        if hasattr(resp, 'text'):
                            result = resp.text if resp.text else ""
                            print(f"Text extracted: {result[:100]}...")
                            return result
                        else:
                            print(f"Response has no 'text' attribute. Full response: {resp}")
                            return str(resp)
                    except Exception as e:
                        print(f"Error calling new Google GenAI API: {e}")
                        raise e
                else:
                    # Fallback to old API
                    cfg = {
                        "candidate_count": 1,
                        "max_output_tokens": self.max_tokens,
                        "temperature": self.temperature,
                        "top_p": 0.95,
                    }
                    resp = self.model.generate_content(prompt, generation_config=cfg)
                    
                    # Debug: Log response structure for troubleshooting
                    print(f"Response type: {type(resp)}")
                    print(f"Response attributes: {dir(resp)}")
                    if hasattr(resp, 'parts'):
                        print(f"Response has {len(resp.parts)} parts")
                    if hasattr(resp, 'candidates'):
                        print(f"Response has {len(resp.candidates)} candidates")
                    
                    # Robust text extraction: support multi-part responses
                    def extract_text(r) -> str:
                        try:
                            # 1) Try the new recommended approach: result.parts
                            parts = getattr(r, 'parts', None)
                            if parts:
                                buf = []
                                for p in parts:
                                    v = getattr(p, 'text', None)
                                    if isinstance(v, str):
                                        buf.append(v)
                                if buf:
                                    return "".join(buf)
                            
                            # 2) Try candidates -> content.parts (fallback for older responses)
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
                            
                            # 3) Try the old .text accessor (for backward compatibility)
                            t = getattr(r, 'text', None)
                            if isinstance(t, str) and t.strip():
                                return t
                            
                            # 4) If all else fails, try to get any text from the response object
                            response_str = str(r)
                            if response_str and response_str != "None":
                                return response_str
                            
                            return "No text content found in response"
                            
                        except Exception as e:
                            print(f"Error extracting text from response: {e}")
                            return f"Error extracting response: {e}"
                    text = extract_text(resp)
                    return text if text else ""
            except Exception as e:
                print(f"Error in text generation: {e}")
                return f"Error generating response: {e}"
        try:
            return await asyncio.wait_for(asyncio.to_thread(_gen), timeout=30.0)  # Increased timeout to 30 seconds
        except asyncio.TimeoutError:
            return "I'm still thinking; here is a brief answer while I finish processing."
        except Exception as e:
            return f"Error generating response: {e}"

# Initialize all models
speech_recognizer = initialize_speech_recognition()
tts_engine = initialize_tts()
gemini_client = GeminiClient(GEMINI_API_KEY, PREFERRED_GEMINI_MODELS, max_tokens=128, temperature=0.7)

# Test TTS model availability
async def test_tts_model():
    """Test if the TTS model is available and working"""
    try:
        # Ensure Gemini client is initialized
        await gemini_client.ensure_initialized()
        
        if not hasattr(gemini_client, 'client'):
            print("❌ Gemini client not available for TTS testing")
            return False
        
        print(f"🧪 Testing TTS model: {TTS_MODEL}")
        
        # Try a simple test call - TTS model expects AUDIO output, not TEXT
        test_resp = gemini_client.client.models.generate_content(
            model=TTS_MODEL,
            contents=[{
                "role": "user",
                "parts": [{"text": "Hello"}]
            }]
        )
        
        print(f"✅ TTS model test successful: {type(test_resp)}")
        print(f"📋 TTS response attributes: {dir(test_resp)}")
        return True
        
    except Exception as e:
        print(f"❌ TTS model test failed: {e}")
        return False

# Audio processing functions
def is_websocket_open(websocket):
    """Safely check if WebSocket connection is still open"""
    try:
        return websocket.state.name != 'CLOSED'
    except AttributeError:
        # Fallback for different websocket implementations
        try:
            return not websocket.closed
        except AttributeError:
            # If we can't determine, assume it's open and let the send operation fail naturally
            return True

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

async def generate_tts_with_gemini(text, session_id):
    """Generate TTS using Gemini TTS model"""
    try:
        if not hasattr(gemini_client, 'client'):
            return None, "Error: Gemini client not available for TTS"
        
        print(f"Generating TTS with Gemini TTS model: {text[:100]}...")
        
        # Use the TTS model for voice generation
        # Use the correct TTS API format - TTS model expects AUDIO output
        resp = None
        try:
            # Try the new Google GenAI API format for TTS
            resp = gemini_client.client.models.generate_content(
                model=TTS_MODEL,
                contents=[{
                    "role": "user",
                    "parts": [{"text": text}]
                }]
            )
            print(f"TTS API call successful")
        except Exception as e:
            print(f"TTS API call failed: {e}")
            # Try alternative format
            try:
                resp = gemini_client.client.models.generate_content(
                    model=TTS_MODEL,
                    contents=text
                )
                print(f"TTS API call successful with alternative format")
            except Exception as alt_error:
                print(f"TTS API call failed with alternative format: {alt_error}")
                return None, f"TTS API call failed: {alt_error}"
        
        print(f"TTS response received: {type(resp)}")
        print(f"TTS response attributes: {dir(resp)}")
        
        # Extract audio data from response - try multiple approaches
        audio_data = None
        
        # Method 1: Direct audio attribute
        if hasattr(resp, 'audio') and resp.audio:
            audio_data = resp.audio
            print("Found audio in direct 'audio' attribute")
        
        # Method 2: Check candidates structure
        elif hasattr(resp, 'candidates') and resp.candidates:
            print(f"Checking {len(resp.candidates)} candidates for audio")
            for i, candidate in enumerate(resp.candidates):
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for j, part in enumerate(candidate.content.parts):
                        if hasattr(part, 'audio') and part.audio:
                            audio_data = part.audio
                            print(f"Found audio in candidate {i}, part {j}")
                            break
                    if audio_data:
                        break
        
        if audio_data:
            # Convert to base64 for transmission
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # Save the audio file for logging
            audio_filename = f"{AUDIO_LOG_DIR}/bot_audio_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            try:
                with open(audio_filename, 'wb') as audio_file:
                    audio_file.write(audio_data)
                print(f"Saved TTS audio: {audio_filename}")
            except Exception as e:
                print(f"Warning: could not save bot audio log: {e}")
            
            return audio_base64, None
        else:
            error_msg = f"TTS response has no audio content. Response: {resp}"
            print(error_msg)
            return None, error_msg
            
    except Exception as e:
        print(f"Error in Gemini TTS: {e}")
        return None, f"Error in Gemini TTS: {e}"

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
                try:
                    # Try to parse as JSON first (for special commands)
                    data = json.loads(message)
                    if data.get("type") == "tts_request" and data.get("text"):
                        # Handle TTS request with Gemini TTS model
                        try:
                            # Generate text response first
                            bot_text = await gemini_client.generate(data["text"])
                            bot_text = bot_text.strip() if isinstance(bot_text, str) else str(bot_text)
                            
                            if not bot_text:
                                bot_text = "I couldn't generate a response. Please try again."
                            
                            # Generate TTS using Gemini TTS model
                            audio_base64, tts_error = await generate_tts_with_gemini(bot_text, session_id)
                            
                            # Send response with audio
                            response_data = {
                                "type": "text",
                                "content": bot_text,
                                "session_id": session_id
                            }
                            
                            if audio_base64:
                                response_data["audio"] = audio_base64
                            elif tts_error:
                                response_data["tts_error"] = tts_error
                            
                            print(f"Sending TTS response: {response_data}")
                            await websocket.send(json.dumps(response_data))
                            
                            # Log the interaction
                            def _log_tts_row():
                                try:
                                    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
                                        writer = csv.writer(f)
                                        writer.writerow([datetime.now().isoformat(), session_id, data["text"], bot_text, "N/A", f"bot_audio_{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav" if audio_base64 else "N/A"])
                                except Exception as e:
                                    print(f"Error logging TTS row: {e}")
                            asyncio.create_task(asyncio.to_thread(_log_tts_row))
                            
                        except Exception as e:
                            error_response = f"Error processing TTS request: {e}"
                            await websocket.send(json.dumps({
                                "type": "text",
                                "content": error_response
                            }))
                        continue
                    elif data.get("type") == "ping":
                        # Handle keep-alive ping
                        try:
                            await websocket.send(json.dumps({
                                "type": "pong",
                                "content": "keep-alive-ack"
                            }))
                        except Exception as e:
                            print(f"Error sending pong: {e}")
                        continue
                    elif data.get("type") == "text":
                        # Handle text message from structured format
                        user_msg = data.get("content", "").strip()
                        if not user_msg:
                            await websocket.send(json.dumps({
                                "type": "text",
                                "content": "Please send a non-empty message."
                            }))
                            continue
                        await process_text_message(websocket, user_msg, session_id, enable_tts=False)
                        continue
                except json.JSONDecodeError:
                    # Handle plain text message (backward compatibility)
                    user_msg = message.strip()
                    if not user_msg:
                        await websocket.send(json.dumps({
                            "type": "text",
                            "content": "Please send a non-empty message."
                        }))
                        continue
                    
                    # Process text message without TTS for faster responses
                    await process_text_message(websocket, user_msg, session_id, enable_tts=False)
                
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

async def process_text_message(websocket, user_msg, session_id, enable_tts=False):
    """Process text message and generate response"""
    try:
        # Check if WebSocket is still open before processing
        if not is_websocket_open(websocket):
            print(f"❌ WebSocket closed, cannot send response for: {user_msg[:50]}...")
            return
            
        bot_text = await gemini_client.generate(user_msg)
        bot_text = bot_text.strip() if isinstance(bot_text, str) else str(bot_text)
        if not bot_text:
            bot_text = "I couldn't generate a response. Please try again."

        # Convert text response to speech using Gemini TTS if requested
        audio_base64, tts_error = (None, None)
        if enable_tts:
            try:
                print(f"Generating TTS for voice response: {bot_text[:100]}...")
                # Try Gemini TTS first
                audio_base64, tts_error = await generate_tts_with_gemini(bot_text, session_id)
                if tts_error:
                    print(f"Gemini TTS failed, falling back to local TTS: {tts_error}")
                    # Fallback to local TTS
                    audio_base64, tts_error = await asyncio.to_thread(text_to_speech, bot_text, session_id)
            except Exception as e:
                print(f"Error with Gemini TTS, using local TTS: {e}")
                # Fallback to local TTS
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
        
        print(f"Sending response: {response_data}")
        
        # Check if WebSocket is still open before sending
        if not is_websocket_open(websocket):
            print(f"❌ WebSocket closed before sending response for: {user_msg[:50]}...")
            return
            
        try:
            await websocket.send(json.dumps(response_data))
            print(f"✅ Response sent successfully to WebSocket")
        except Exception as send_error:
            print(f"❌ Error sending response to WebSocket: {send_error}")
            # Try to send just the text if the full response fails
            try:
                if is_websocket_open(websocket):
                    simple_response = {
                        "type": "text",
                        "content": bot_text,
                        "session_id": session_id
                    }
                    await websocket.send(json.dumps(simple_response))
                    print(f"✅ Simple response sent successfully")
                else:
                    print(f"❌ WebSocket closed, cannot send simple response")
            except Exception as simple_error:
                print(f"❌ Simple response also failed: {simple_error}")
        
    except Exception as e:
        bot_text = f"Error generating response: {e}"
        print(f"❌ Error in process_text_message: {e}")
        
        # Only try to send error if WebSocket is still open
        if is_websocket_open(websocket):
            try:
                await websocket.send(json.dumps({
                    "type": "text",
                    "content": bot_text
                }))
            except Exception as send_error:
                print(f"❌ Could not send error response: {send_error}")
        else:
            print(f"❌ WebSocket closed, cannot send error response")

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
        
        print(f"🔄 Processing transcribed text: {transcribed_text}")
        # Process the transcribed text with TTS enabled for voice responses
        await process_text_message(websocket, transcribed_text, session_id, enable_tts=ENABLE_TTS_FOR_VOICE)
        print(f"✅ Voice message processing completed")
        
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
    
    # Test TTS model availability
    print("Testing TTS model availability...")
    # Wait for Gemini client to initialize first
    await gemini_client.ensure_initialized()
    tts_available = await test_tts_model()
    if tts_available:
        print("✅ TTS model is available and working")
    else:
        print("❌ TTS model is not available - voice responses will not have audio")
    
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
        if GEMINI_API_KEY:
            print(f"Using Gemini API key: {GEMINI_API_KEY[:10]}...")
        else:
            print("Warning: GEMINI_API_KEY not set. Please set it in your environment variables.")
            print("You can get a free API key from: https://makersuite.google.com/app/apikey")
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
    try:
        httpd = HTTPServer(('127.0.0.1', 8081), ChatLogHandler)
        print('HTTP server running at http://127.0.0.1:8081/chat_history')
        httpd.serve_forever()
    except PermissionError:
        print('Warning: Port 8081 is not available. HTTP server disabled.')
        print('You can still use the WebSocket server for chat functionality.')
    except Exception as e:
        print(f'Warning: HTTP server failed to start: {e}')
        print('You can still use the WebSocket server for chat functionality.')

if __name__ == "__main__":
    threading.Thread(target=start_http_server, daemon=True).start()
    asyncio.run(main())
