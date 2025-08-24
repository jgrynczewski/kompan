# ADR-0001: Claude API Integration for Intelligent Conversations

**Date**: 2024-08-24  
**Status**: Accepted  
**Deciders**: Development Team  

## Context

The application initially used basic offline conversation patterns that were repetitive, formal, and didn't lead to meaningful conclusions. Users reported conversations felt like "medical questionnaires" rather than natural dialogue.

## Decision

Integrate Claude 3.5 Sonnet API for intelligent, contextual conversations instead of relying solely on hardcoded patterns.

## Rationale

### Why Claude API:
- **Natural conversation flow** - Claude can maintain context and adapt to responses
- **Polish language support** - Native support for conversational Polish
- **Contextual intelligence** - Understands user emotions and needs
- **Meaningful conclusions** - Can summarize conversations for caregivers
- **Personalization** - Adapts conversation style based on user responses

### Implementation Details:
- **Model**: `claude-3-5-sonnet-20241022` (latest stable version)
- **Security**: API key stored in `.env` file with `python-dotenv`
- **Fallback**: Offline patterns when API unavailable
- **Error handling**: Graceful degradation to ensure system always works

## Consequences

### Positive:
- ✅ Natural, engaging conversations
- ✅ Contextual awareness and memory
- ✅ Intelligent summaries for caregivers
- ✅ Adaptive conversation flow
- ✅ Better user experience

### Negative:
- ❌ Dependency on external API
- ❌ Requires internet connection for full functionality
- ❌ API costs (though minimal for target usage)
- ❌ Need for API key management

### Mitigations:
- Comprehensive offline fallback system
- Secure API key storage
- Error recovery mechanisms
- Local conversation patterns as backup

## Implementation Status

- ✅ Claude client implemented (`src/ai/claude_client.py`)
- ✅ API key security with `.env` file
- ✅ Model compatibility updated to latest version
- ✅ Fallback system tested and working
- ✅ Polish conversation prompts optimized
- ✅ Integration with conversation manager complete

## Related Decisions

- [ADR-0002: Desktop Application Architecture](#)
- [ADR-0003: TTS Multi-Engine Fallback](#)