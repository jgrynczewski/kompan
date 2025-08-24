# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records documenting the key decisions made during the development of Kompan, an AI communication assistant for people with severe physical disabilities.

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-claude-api-integration.md) | Claude API Integration for Intelligent Conversations | ✅ Accepted | 2024-08-24 |
| [0002](0002-desktop-application-architecture.md) | Desktop Application Architecture for Assistive Technology | ✅ Accepted | 2024-08-24 |
| [0003](0003-tts-multi-engine-fallback.md) | Multi-Engine TTS Fallback System for Polish Language | ✅ Accepted | 2024-08-24 |
| [0004](0004-user-context-database.md) | User Context Database for Personalized Conversations | 🔄 Proposed | 2024-08-24 |

## Decision Status Legend

- ✅ **Accepted** - Decision has been made and implemented
- 🔄 **Proposed** - Decision proposed but not yet implemented
- ❌ **Rejected** - Decision considered but rejected
- 🚫 **Deprecated** - Decision was accepted but is now superseded

## Key Architectural Decisions Summary

### Core Technology Stack
- **Backend**: FastAPI with WebSocket support
- **AI Integration**: Claude 3.5 Sonnet API for intelligent conversations  
- **TTS System**: Multi-engine fallback (edge-tts → gTTS → pyttsx3 → pre-recorded)
- **Frontend**: Desktop application (Electron recommended) for assistive technology features
- **Data Storage**: JSON for user context, SQLite for conversation history
- **Deployment**: Docker container with X11 support for desktop apps

### Critical Design Principles
1. **Accessibility First** - Every feature designed for users with severe physical disabilities
2. **Never Leave User Stuck** - Multiple fallback systems and emergency recovery
3. **Always-On Availability** - Offline modes and local backups for critical functionality
4. **Privacy by Design** - Local data storage with user consent and control
5. **Progressive Enhancement** - Basic functionality works without advanced features

### Security Considerations
- API keys stored in `.env` files with proper `.gitignore`
- Local data storage to avoid cloud privacy concerns
- Encrypted sensitive medical information
- Emergency access protocols for caregivers

## Creating New ADRs

When making significant architectural decisions:

1. **Create new ADR file**: `docs/adr/NNNN-short-title.md`
2. **Use the template format**: Context, Decision, Rationale, Consequences
3. **Update this README**: Add entry to the index table
4. **Cross-reference**: Link related ADRs
5. **Get review**: Discuss with stakeholders before marking as Accepted

### ADR Template
```markdown
# ADR-NNNN: [Title]

**Date**: YYYY-MM-DD  
**Status**: [Proposed|Accepted|Rejected|Deprecated]  
**Deciders**: [List of people involved]  

## Context
[What is the issue that we're seeing that is motivating this decision or change?]

## Decision
[What is the change that we're proposing or have agreed to implement?]

## Rationale
[Why are we making this decision? What alternatives were considered?]

## Consequences
[What becomes easier or more difficult to do because of this change?]

## Implementation Status
- [ ] Task 1
- [ ] Task 2

## Related Decisions
- [ADR-XXXX: Related Decision](#)
```

---

*For questions about these architectural decisions, please refer to the individual ADR documents or contact the development team.*