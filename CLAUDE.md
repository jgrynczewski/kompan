# CLAUDE.md - Project Knowledge Base for Kompan

This file contains essential project knowledge for Claude AI to understand the current state, architecture, and requirements for future development iterations.

## Project Overview

**Kompan** is an AI-powered communication assistant designed specifically for people with severe physical disabilities who can only respond with yes/no answers. The application provides intelligent conversations through scanning interface with audio cues.

### Target Users
- People with conditions like ALS, severe cerebral palsy, locked-in syndrome
- Users who can only move eyes or have minimal motor control
- Communication limited to yes/no responses via clicking or scanning

### Core Requirements
1. **Never leave user stuck** - Always provide way to continue or restart
2. **Accessible interface** - Large buttons, audio cues, scanning system  
3. **Intelligent conversations** - Contextual, meaningful dialogue
4. **Always-on-top** - Must be visible over all other applications
5. **Global input capture** - Click anywhere = select highlighted option

## Current Architecture Status

### ✅ PHASE 1 - COMPLETED (Web-based MVP)

#### Working Components:
- **FastAPI Backend** (`src/main.py`) - WebSocket + HTTP API
- **Multi-engine TTS** (`src/tts/engine.py`) - Polish language support
- **Claude AI Integration** (`src/ai/claude_client.py`) - Intelligent conversations  
- **Conversation Manager** (`src/conversation/manager.py`) - Session handling
- **Web GUI** (`src/gui/`) - Scanning interface with YES/NO buttons
- **Docker Container** - Fully containerized deployment

#### Recent Critical Fixes Applied:
1. **Conversation ending after first TAK** - Extended offline patterns to 4 rounds
2. **Missing audio cues** - Added HTTP fallback for WebSocket failures
3. **TTS for end messages** - Added TTS call in onConversationEnd()
4. **Claude API integration** - Secure .env key storage with python-dotenv
5. **Model compatibility** - Updated to claude-3-5-sonnet-20241022
6. **First TAK audio cue** - Added playAudioCue() in startScanning()

### 🚧 PHASE 2 - PENDING (Desktop Application)

#### Required Transitions:
- **Web → Desktop App** - For assistive technology features
- **Always-on-top window** - Top-right corner overlay
- **Global click capture** - Any click = select highlighted button
- **System-wide control** - Block other app interactions
- **User context system** - Personal profiles and conversation memory

## File Structure & Key Components

```
kompan/
├── src/
│   ├── main.py                    # FastAPI app with WebSocket/HTTP
│   ├── ai/claude_client.py        # Claude 3.5 Sonnet integration
│   ├── tts/engine.py             # Multi-engine TTS (edge-tts/gTTS/pyttsx3)
│   ├── conversation/manager.py    # Session & pattern management
│   └── gui/                      # Web interface (HTML/CSS/JS)
│       ├── index.html            # Main interface with YES/NO buttons
│       ├── styles.css            # Responsive design + animations
│       └── app.js               # Scanning logic + WebSocket handling
├── config/settings.json          # Application configuration
├── data/                         # Conversation logs (conversation_*.json)
├── docs/adr/                     # Architecture Decision Records
├── .env                         # Claude API key (secure storage)
├── .gitignore                   # Prevents committing sensitive files
├── Dockerfile                   # Container deployment
├── requirements.txt             # Python dependencies
└── TODO.md                     # Current development status
```

## Technical Implementation Details

### Claude AI Integration
```python
# Current working model (latest version)
model = "claude-3-5-sonnet-20241022"

# API key loaded from .env file
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')

# System prompt optimized for Polish assistive conversations
system_prompt = """
Jesteś asystentem komunikacyjnym dla osoby z poważnymi niepełnosprawnościami fizycznymi.
Prowadzisz całą rozmowę - musisz wydedukować co osoba chce przekazać.
Zadawaj pytania tak, by krok po kroku zrozumieć jej myśli i potrzeby.
"""
```

### TTS Fallback Hierarchy
1. **edge-tts** (Primary) - High-quality Polish neural voices
2. **gTTS** (Secondary) - Google TTS Polish voice  
3. **pyttsx3** (Tertiary) - System TTS offline
4. **Pre-recorded** (Fallback) - Critical phrases backup

### Conversation Flow
1. **Start scanning** - Visual highlight + audio cue ("tak"/"nie")
2. **User clicks** - Selects highlighted option
3. **Process response** - Send to Claude or offline patterns
4. **Generate question** - AI-powered contextual follow-up
5. **TTS playback** - Read question aloud
6. **Resume scanning** - Continue cycle

### Error Handling Strategy
- **WebSocket fails** → HTTP API fallback
- **Claude API fails** → Offline conversation patterns  
- **TTS engine fails** → Next engine in hierarchy
- **Complete failure** → Emergency restart mechanism
- **User stuck** → Click anywhere recovery

## Configuration Management

### Key Settings (`config/settings.json`):
```json
{
  "scanning_interval": 2.0,        # Button highlight timing
  "tts_engine": "auto",            # TTS engine selection
  "language": "pl",                # Polish language
  "gui_port": 8082,               # Web interface port
  "conversation_history_days": 30  # Log retention
}
```

### Environment Variables (`.env`):
```bash
CLAUDE_API_KEY=sk-ant-api03-[your-key-here]
```

## Phase 2 Architecture Requirements

### Desktop Application Features Needed:
1. **Always-on-top window** - Cannot be minimized or hidden
2. **Global mouse capture** - Any screen click = button selection
3. **Keyboard blocking** - Disable Alt+Tab, other shortcuts
4. **System tray integration** - For caregiver controls
5. **Emergency exit** - Caregiver override shortcuts (Ctrl+Shift+E)

### Recommended Desktop Stack:
- **Primary**: Electron (familiar web tech, proven in assistive software)
- **Alternative**: Tauri (Rust-based, smaller footprint)
- **Fallback**: Python + Tkinter (lightweight, built-in)

### User Context Database Schema:
```json
{
  "personal": {
    "name": "string",
    "condition": "string", 
    "communication_level": "yes_no_only"
  },
  "medical": {
    "mobility": "wheelchair_dependent",
    "pain_areas": ["array"],
    "medications": ["array"]
  },
  "social": {
    "primary_caregiver": "string",
    "family": ["array"],
    "friends": ["array"]
  },
  "preferences": {
    "topics_of_interest": ["array"],
    "sensitive_topics": ["array"]
  }
}
```

## Development Guidelines

### Code Style & Patterns:
- **Error handling**: Always provide fallbacks
- **Logging**: Comprehensive debug info for troubleshooting  
- **Accessibility**: Test with screen readers, high contrast
- **Performance**: Minimize delays in scanning/response cycles
- **Security**: Never commit API keys or sensitive data

### Testing Requirements:
- **Audio cue timing** - Verify "tak"/"nie" spoken correctly
- **WebSocket recovery** - Test connection failures
- **TTS fallbacks** - Simulate engine failures
- **Conversation flow** - Test Claude API responses
- **Emergency recovery** - Verify user never gets stuck

### Deployment Strategy:
```bash
# Docker container with audio support
docker run -d \
  -p 8082:8082 \
  -v ./data:/app/data \
  -v ./config:/app/config \
  --device /dev/snd \
  --name kompan \
  kompan:latest
```

## Critical Issues to Remember

### Fixed Issues (Don't Regress):
- ✅ Conversations ending after first response
- ✅ First "TAK" audio cue not playing
- ✅ WebSocket failures blocking functionality
- ✅ Claude API authentication errors
- ✅ Missing TTS for conversation end messages

### Known Working Patterns:
- HTTP API fallback when WebSocket fails
- Emergency restart mechanism when system stuck
- Multi-engine TTS with graceful degradation
- Offline conversation patterns as Claude backup

## Future Development Priorities

### Phase 2 - High Priority:
1. **Desktop application conversion** (Electron recommended)
2. **User context database** with automatic Claude updates
3. **Always-on-top overlay window** (top-right corner)  
4. **Global input capture** (click anywhere = select)
5. **Comprehensive logging** to dedicated files

### Phase 3 - Medium Priority:
1. **Caregiver dashboard** for conversation summaries
2. **Enhanced offline patterns** for better conversations
3. **Multi-language support** beyond Polish
4. **Voice activation** as alternative input method

## Communication Protocols

### WebSocket Messages:
```javascript
// Start conversation
{type: 'start_conversation'}

// Send response
{type: 'response', value: true/false}

// Audio cue request  
{type: 'audio_cue', text: 'tak'/'nie'}

// System restart
{type: 'restart'}
```

### HTTP API Endpoints:
- `POST /api/respond` - Process yes/no response
- `POST /api/tts/speak` - Direct TTS request
- `GET /api/settings` - Get configuration
- `POST /api/settings` - Update configuration

## Emergency Procedures

### User Recovery Actions:
1. **Click anywhere** when system not scanning → Emergency restart
2. **Wait 10 seconds** during errors → Automatic recovery
3. **Refresh browser** → Restart web interface
4. **Container restart** → `docker restart kompan`

### Caregiver Override:
- **Ctrl+Shift+E** - Emergency exit (future desktop app)
- **Ctrl+Shift+R** - Force restart conversation
- **Ctrl+Shift+S** - Open settings panel

## Success Metrics

### Functional Requirements:
- [ ] User never gets stuck without recovery option
- [x] Audio cues play reliably for each scanning cycle
- [x] Conversations are intelligent and contextual
- [x] TTS works in Polish across multiple engines
- [x] System recovers from network/API failures

### Performance Requirements:
- Scanning cycle: 2 seconds (configurable)
- TTS response: < 3 seconds
- Claude API response: < 10 seconds with fallback
- Emergency recovery: < 5 seconds

---

*This document serves as the primary knowledge base for understanding Kompan's current implementation and future development requirements. Update this file when significant architectural changes are made.*

**Last Updated**: 2024-08-24  
**Current Status**: Phase 1 Complete, Phase 2 Planning  
**Next Priority**: Desktop application architecture implementation