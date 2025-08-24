# ADR-0002: Desktop Application Architecture for Assistive Technology

**Date**: 2024-08-24  
**Status**: Accepted  
**Deciders**: Development Team, User Requirements  

## Context

The application needs to function as assistive technology for people with severe physical disabilities who can only respond yes/no. Critical requirements emerged:

1. **Always-on-top window** - Must stay visible over all other applications
2. **Global input capture** - Click anywhere on screen = select highlighted option
3. **System-wide control** - Block other applications from interfering
4. **Emergency accessibility** - Users cannot be left in a stuck state

Initial web-based approach cannot meet these system-level requirements.

## Decision

Convert from web application to desktop application architecture while maintaining containerized backend.

## Architecture Comparison

| Requirement | Web App | Desktop App |
|-------------|---------|-------------|
| Always-on-top | ❌ Limited browser control | ✅ Native window management |
| Global mouse capture | ❌ Browser sandbox restrictions | ✅ System-level event handling |
| Keyboard blocking | ❌ Security restrictions | ✅ Global hotkey capture |
| Cross-platform | ✅ Browser compatibility | ✅ Electron/Tauri support |
| System integration | ❌ Limited OS access | ✅ Full OS integration |
| Container deployment | ✅ Direct web serving | ✅ X11 forwarding support |

## Recommended Technology Stack

### Option 1: Electron (Recommended)
- **Pros**: Web technologies (HTML/CSS/JS), extensive documentation, proven in assistive tech
- **Cons**: Higher memory usage, larger bundle size
- **Libraries**: `electron`, `electron-builder`

### Option 2: Tauri (Alternative)
- **Pros**: Rust backend, smaller bundle size, better performance
- **Cons**: Newer ecosystem, steeper learning curve
- **Libraries**: `tauri`, `wry`

### Option 3: Python + Tkinter (Fallback)
- **Pros**: Lightweight, built-in, easy debugging
- **Cons**: Less modern UI, platform-specific styling
- **Libraries**: `tkinter`, `pynput`

## Implementation Plan

### Phase 1: Desktop Shell
1. Create Electron wrapper around existing web interface
2. Implement always-on-top window positioning (top-right corner)
3. Add global click capture functionality
4. Maintain FastAPI backend for business logic

### Phase 2: System Integration
1. Block other application interactions
2. Emergency keyboard shortcuts for caregivers
3. Window management (prevent minimize/close)
4. System tray integration

### Architecture:
```
┌─────────────────────────────────────────┐
│ Docker Container                        │
│ ┌─────────────────────────────────────┐ │
│ │ Electron Desktop App                │ │
│ │ ┌─────────────┐ ┌─────────────────┐ │ │
│ │ │     TAK     │ │      NIE       │ │ │
│ │ └─────────────┘ └─────────────────┘ │ │
│ │           Always On Top             │ │
│ │        Global Click Capture         │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ FastAPI Backend (Unchanged)         │ │
│ │ • TTS Engine                        │ │
│ │ • Claude Integration               │ │
│ │ • Conversation Manager             │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Consequences

### Positive:
- ✅ Can implement required assistive technology features
- ✅ Always-on-top window guaranteed
- ✅ Global input capture possible
- ✅ System-wide keyboard control
- ✅ Better accessibility compliance
- ✅ Maintains existing backend logic

### Negative:
- ❌ More complex deployment (requires display server)
- ❌ Platform-specific considerations
- ❌ Additional dependencies (Electron/Node.js)
- ❌ Larger application footprint

### Mitigations:
- Container deployment with X11 forwarding
- Cross-platform testing on Windows/macOS/Linux
- Fallback to web interface if desktop fails
- Comprehensive documentation for setup

## Container Strategy

```dockerfile
# Add desktop dependencies
RUN apt-get update && apt-get install -y \
    xvfb \
    x11-utils \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2

# Install Node.js for Electron
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

# Copy and install desktop app
COPY desktop/ /app/desktop/
RUN cd /app/desktop && npm install

# Start script with display server
CMD ["./start-desktop.sh"]
```

## Implementation Status

- 🔲 Desktop application framework selection
- 🔲 Electron/Tauri prototype
- 🔲 Always-on-top window implementation
- 🔲 Global click capture
- 🔲 Container integration
- 🔲 Cross-platform testing

## Related Decisions

- [ADR-0001: Claude API Integration](0001-claude-api-integration.md)
- [ADR-0003: TTS Multi-Engine Fallback](#)
- [ADR-0004: User Context Database](#)