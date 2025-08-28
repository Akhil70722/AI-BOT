# 🔧 Troubleshooting Guide

## Common Issues and Solutions

### 1. **Missing GEMINI_API_KEY Error**

**Problem**: `Warning: GEMINI_API_KEY missing.`

**Solution**:
1. Run the configuration script:
   ```bash
   python configure_api.py
   ```
2. Follow the prompts to enter your API key
3. Get a free API key from: https://makersuite.google.com/app/apikey

### 2. **Port Permission Error**

**Problem**: `PermissionError: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions`

**Solution**:
- The server now automatically tries port 8081 instead of 8080
- If you still get permission errors, try a different port by editing `server.py`

### 3. **FFmpeg Warning**

**Problem**: `RuntimeWarning: Couldn't find ffmpeg or avconv - defaulting to ffmpeg, but may not work`

**Solution**:
1. **Windows**: Run `install_ffmpeg.bat` or use:
   ```bash
   winget install ffmpeg
   ```
2. **macOS**: `brew install ffmpeg`
3. **Linux**: `sudo apt install ffmpeg`

### 4. **Missing Dependencies**

**Problem**: Import errors for various packages

**Solution**:
```bash
pip install -r requirements.txt
```

### 5. **Audio Processing Issues**

**Problem**: Audio recording or playback not working

**Solution**:
1. Ensure ffmpeg is installed (see above)
2. Check microphone permissions in your browser
3. Try refreshing the page
4. Check browser console for errors

### 6. **Server Won't Start**

**Problem**: Various startup errors

**Solution**:
1. Check all dependencies are installed
2. Ensure API key is configured
3. Try running with verbose output:
   ```bash
   python -v server.py
   ```

## Quick Fix Commands

```bash
# Install all dependencies
pip install -r requirements.txt

# Configure API key
python configure_api.py

# Install ffmpeg (Windows)
install_ffmpeg.bat

# Start server
python server.py
```

## Getting Help

1. Check this troubleshooting guide
2. Look at the error messages in the terminal
3. Check the browser console for client-side errors
4. Ensure all files are in the correct directory structure

## System Requirements

- **Python**: 3.8 or higher
- **OS**: Windows 10+, macOS 10.14+, or Linux
- **Browser**: Modern browser with WebSocket support
- **Audio**: Microphone and speakers/headphones
- **Internet**: Required for Gemini AI API calls
