# Kompan - AI Communication Assistant (Revised Plan)

## Project Overview
AI-based communication assistant for people with severe physical disabilities who can only respond yes/no. Containerized for compatibility with old systems.

## Phase 1: Single Container MVP (Today's Target)

### Architecture
- **Single Container**: GUI + HTTP server integrated
- **Web-based GUI**: HTML/CSS/JS served by FastAPI
- **Browser Interface**: Opens automatically in system browser
- **Polish TTS**: Guaranteed support via multiple fallback engines

### Core Components

#### 1. Container Structure
```
Dockerfile: Python + FastAPI + TTS engines
Port 8080: Web interface
Port 8081: HTTP API for external processes
Volume: ./data for conversation history
Volume: ./config for settings
```

#### 2. Web GUI Interface
- **Large YES/NO buttons** with clear scanning highlights
- **Visual feedback**: Bright colors, clear typography
- **Status display**: Current question, conversation state
- **Responsive design**: Works on any screen size

#### 3. Scanning System
- **Configurable timing** (default 2s)
- **Audio cues**: TTS saying "tak"/"nie" in Polish
- **Pause during questions**: No scanning while TTS speaks
- **Visual indicators**: Clear highlight progression

#### 4. Polish TTS Engine (Multi-layered Approach)
```
Priority 1: edge-tts (Microsoft Edge TTS - excellent Polish)
Priority 2: gTTS (Google TTS - reliable fallback)
Priority 3: pyttsx3 with Polish voice (system fallback)
Fallback: Pre-recorded audio files for critical phrases
```

#### 5. AI Conversation Engine
- **Claude API integration** with error handling
- **Conversation context** maintained in session
- **Polish language** prompts and responses
- **Conversation logging** for sharing with caregivers
- **Offline mode**: Basic conversation patterns when API unavailable

#### 6. HTTP API Server (Integrated)
- **FastAPI embedded** in main application
- **External control** endpoints for Python processes
- **Conversation state** management
- **Real-time updates** via WebSocket

### Technical Implementation

#### TTS Testing Strategy
1. Test all TTS engines during container startup
2. Select best available Polish voice
3. Fallback cascade if primary fails
4. Audio quality validation

#### Error Handling
- **API failures**: Graceful degradation to offline mode
- **TTS failures**: Automatic engine switching
- **Network issues**: Local conversation patterns
- **Emergency restart**: Button to reset conversation

#### Configuration
```json
{
  "scanning_interval": 2.0,
  "tts_engine": "auto",
  "language": "pl",
  "api_timeout": 10,
  "conversation_history_days": 30
}
```

### Installation & Deployment
```bash
# One command installation
docker run -d \
  -p 8080:8080 \
  -p 8081:8081 \
  -v ./data:/app/data \
  -v ./config:/app/config \
  --name kompan \
  kompan:latest

# Auto-opens browser to localhost:8080
```

## Directory Structure
```
kompan/
├── Dockerfile
├── requirements.txt
├── src/
│   ├── main.py              # FastAPI app + GUI server
│   ├── gui/                 # Web interface (HTML/CSS/JS)
│   ├── tts/                 # Multi-engine TTS handler
│   ├── ai/                  # Claude integration
│   ├── conversation/        # Conversation logic
│   └── api/                 # HTTP API endpoints
├── config/
│   └── settings.json
├── data/                    # Conversation history
├── install.sh / install.bat
└── README.md
```

## Success Criteria for Today
1. **Working container** with web GUI
2. **Quality Polish TTS** (tested with multiple engines)
3. **Scanning interface** with proper timing
4. **Basic Claude conversation** (5+ question exchanges)
5. **HTTP API** for external control
6. **One-command installation**
7. **Error recovery** for common failures

## Key Improvements from Review
- Single container (simplified deployment)
- Multi-engine TTS with Polish guarantee
- Web-based GUI (platform independent)
- Comprehensive error handling
- Offline conversation fallbacks
- Real-time configuration updates

This approach ensures reliability on old systems while maintaining the core conversation experience!