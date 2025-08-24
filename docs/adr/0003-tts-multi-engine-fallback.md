# ADR-0003: Multi-Engine TTS Fallback System for Polish Language

**Date**: 2024-08-24  
**Status**: Accepted  
**Deciders**: Development Team, Accessibility Requirements  

## Context

Text-to-Speech is critical for accessibility in this assistive technology application. Users with severe physical disabilities rely entirely on audio cues to know when scanning begins and which option is highlighted. TTS failure means complete loss of functionality.

Polish language support is essential, and different TTS engines have varying quality and availability across platforms.

## Decision

Implement a multi-engine TTS system with automatic fallback hierarchy for Polish language support.

## TTS Engine Priority Hierarchy

### 1. edge-tts (Primary)
- **Quality**: Excellent Polish voices (natural sounding)
- **Availability**: Requires internet connection
- **Speed**: Fast response times
- **Reliability**: High when internet available
- **Voices**: Multiple Polish options including neural voices

### 2. gTTS (Secondary)
- **Quality**: Good Polish voice quality
- **Availability**: Requires internet connection  
- **Speed**: Moderate response times
- **Reliability**: Very stable Google infrastructure
- **Voices**: Standard Polish voice

### 3. pyttsx3 (Tertiary)
- **Quality**: Platform-dependent (varies by OS)
- **Availability**: Offline, always available
- **Speed**: Fast, no network delay
- **Reliability**: High offline reliability
- **Voices**: Uses system voices (SAPI/espeak/nsss)

### 4. Pre-recorded Audio (Fallback)
- **Quality**: Professional recording possible
- **Availability**: Always available offline
- **Speed**: Instant playback
- **Reliability**: 100% guaranteed
- **Coverage**: Limited to critical phrases ("tak", "nie", emergency messages)

## Implementation Architecture

```python
class PolishTTSHandler:
    def __init__(self):
        self.engines = [
            EdgeTTSEngine(),
            GTTSEngine(), 
            Pyttsx3Engine(),
            PrerecordedAudioEngine()
        ]
    
    async def speak(self, text: str) -> bool:
        for engine in self.engines:
            if await engine.is_available():
                if await engine.speak(text):
                    self.log_success(engine.name)
                    return True
                else:
                    self.log_failure(engine.name)
            else:
                self.log_unavailable(engine.name)
        
        self.log_total_failure()
        return False
```

## Engine Selection Logic

### Initialization Phase:
1. Test all engines for Polish language support
2. Verify audio output capabilities
3. Rank engines by quality and availability
4. Cache working configurations

### Runtime Phase:
1. Try primary engine (edge-tts)
2. If fails, immediately try secondary (gTTS)
3. If fails, fallback to tertiary (pyttsx3)
4. If all fail, use pre-recorded audio for critical phrases
5. Log failures for debugging

### Health Check:
- Periodic engine availability testing
- Automatic re-ranking based on success rates
- Connection status monitoring for online engines

## Configuration

```json
{
  "tts_engine": "auto",
  "tts_config": {
    "edge_tts": {
      "voice": "pl-PL-ZofiaNeural",
      "rate": "medium",
      "volume": "100"
    },
    "gtts": {
      "lang": "pl",
      "slow": false
    },
    "pyttsx3": {
      "rate": 150,
      "volume": 1.0,
      "voice_id": "polish"
    },
    "prerecorded": {
      "base_path": "/app/audio/",
      "format": "wav"
    }
  },
  "fallback_timeout": 3.0,
  "retry_attempts": 2
}
```

## Critical Audio Phrases

Essential phrases that must always work (pre-recorded fallback):
- **"tak"** - Yes highlighting
- **"nie"** - No highlighting  
- **"rozpoczynam skanowanie"** - Starting scan
- **"błąd systemu"** - System error
- **"kliknij aby kontynuować"** - Click to continue

## Error Handling Strategy

### WebSocket Failures:
- HTTP API fallback for TTS requests
- Direct engine calls when WebSocket down
- Emergency audio cue delivery

### Engine Failures:
```python
# Cascade failure handling
try:
    await edge_tts.speak(text)
except NetworkError:
    try:
        await gtts.speak(text)
    except NetworkError:
        await pyttsx3.speak(text)  # Offline guaranteed
```

### Complete TTS Failure:
- Visual-only mode with enhanced highlighting
- Emergency restart mechanisms
- Caregiver notification systems

## Consequences

### Positive:
- ✅ Guaranteed Polish TTS availability
- ✅ High-quality voice output when possible
- ✅ Offline operation capability
- ✅ Graceful degradation
- ✅ Critical phrase backup system
- ✅ Self-healing architecture

### Negative:
- ❌ Increased complexity
- ❌ Multiple dependencies
- ❌ Storage space for pre-recorded audio
- ❌ Maintenance of multiple engine configs

### Mitigations:
- Comprehensive testing suite
- Engine health monitoring
- Automatic fallback verification
- Clear logging for troubleshooting

## Testing Strategy

### Unit Tests:
- Each engine individually
- Polish language support verification
- Fallback chain testing

### Integration Tests:
- Network failure simulation
- Engine unavailability scenarios
- Audio output verification

### Accessibility Tests:
- Audio cue timing validation
- Volume level consistency
- Critical phrase availability

## Implementation Status

- ✅ Multi-engine TTS handler implemented
- ✅ Edge-TTS integration complete
- ✅ gTTS fallback working
- ✅ pyttsx3 system voice support
- ✅ HTTP fallback for WebSocket failures
- ✅ Engine selection and ranking
- 🔲 Pre-recorded audio fallback system
- 🔲 Engine health monitoring
- 🔲 Comprehensive testing suite

## Related Decisions

- [ADR-0001: Claude API Integration](0001-claude-api-integration.md)
- [ADR-0002: Desktop Application Architecture](0002-desktop-application-architecture.md)