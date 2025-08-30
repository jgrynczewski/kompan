# Kompan - Simplified User Context Plan

## Overview

Simple system to provide Kompan with basic user information for personalized conversations. Information is manually delivered and stored locally. Future extensibility for auto-discovery during conversations.

## Core Requirements

1. **Manual Initial Setup**: Caregiver provides basic user information
2. **Simple Storage**: JSON file in Docker volume
3. **Conversation Integration**: Claude uses user info in conversations
4. **Future Ready**: Easy to extend with auto-discovery features

## Simple User Context Schema

**Storage**: `~/kompan/data/user_info.json` (Docker volume)

```json
{
  "user": {
    "name": "Jan Kowalski",
    "preferred_name": "Janek",
    "age": 45,
    "gender": "male",
    "condition": "ALS",
    "family": {
      "spouse": "Maria Kowalska",
      "children": ["Anna (16)", "Tomasz (12)"]
    },
    "interests": ["football", "books", "nature documentaries"],
    "daily_routine": {
      "wake_up": "08:00",
      "lunch": "13:00",
      "sleep": "22:00"
    },
    "medical": {
      "pain_areas": ["back", "legs"],
      "medications": ["Riluzol"],
      "therapies": ["physiotherapy", "speech therapy"]
    }
  },
  "meta": {
    "created": "2024-08-30T12:00:00Z",
    "last_updated": "2024-08-30T12:00:00Z",
    "version": 1
  }
}
```

## Implementation

### 1. Simple Context Service

```python
# src/context/user_context.py
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class UserContext:
    def __init__(self, data_path: str = "data/user_info.json"):
        self.data_path = Path(data_path)
        self._context_cache = None
        
    def load_user_info(self) -> Dict[str, Any]:
        """Load user information from JSON file"""
        if self._context_cache:
            return self._context_cache
            
        if not self.data_path.exists():
            logging.warning("No user info found, using default context")
            return self._get_default_context()
            
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self._context_cache = json.load(f)
                return self._context_cache
        except Exception as e:
            logging.error(f"Failed to load user info: {e}")
            return self._get_default_context()
    
    def get_user_name(self) -> str:
        """Get user's name for conversation personalization"""
        context = self.load_user_info()
        return context.get("user", {}).get("name", "Użytkowniku")
    
    def get_user_summary(self) -> str:
        """Get user summary for Claude prompts"""
        context = self.load_user_info()
        user = context.get("user", {})
        
        summary = f"""
        INFORMACJE O UŻYTKOWNIKU:
        Imię: {user.get('name', 'Nieznane')}
        Wiek: {user.get('age', 'Nieznany')}
        Stan zdrowia: {user.get('condition', 'Nieznany')}
        Rodzina: {', '.join(user.get('family', {}).get('children', []))}
        Zainteresowania: {', '.join(user.get('interests', []))}
        """
        return summary.strip()
    
    def _get_default_context(self) -> Dict[str, Any]:
        """Return default context when no user info exists"""
        return {
            "user": {
                "name": "Użytkowniku",
                "condition": "niepełnosprawność fizyczna"
            },
            "meta": {
                "created": datetime.now().isoformat(),
                "version": 1
            }
        }
```

### 2. Claude Integration

```python
# src/ai/claude_client.py (modified)
class ClaudeClient:
    def __init__(self, api_key: str, user_context: UserContext):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.user_context = user_context
    
    async def create_conversation_prompt(self, user_response: bool) -> str:
        """Create personalized conversation prompt"""
        user_summary = self.user_context.get_user_summary()
        user_name = self.user_context.get_user_name()
        
        system_prompt = f"""
        {user_summary}
        
        Jesteś asystentem komunikacyjnym dla {user_name} z poważnymi niepełnosprawnościami fizycznymi.
        Prowadzisz całą rozmowę - musisz wydedukować co {user_name} chce przekazać.
        Zadawaj pytania tak, by krok po kroku zrozumieć jego myśli i potrzeby.
        Używaj imienia {user_name} w rozmowie.
        """
        
        return system_prompt
```

### 3. Manual Setup Process

**Step 1**: Create user info file manually
```bash
# Caregiver creates this file
mkdir -p ~/kompan/data
nano ~/kompan/data/user_info.json
```

**Step 2**: Fill in user information
```json
{
  "user": {
    "name": "Jan Kowalski",
    "preferred_name": "Janek", 
    "age": 45,
    "gender": "male",
    "condition": "ALS",
    "family": {
      "spouse": "Maria Kowalska",
      "children": ["Anna (16)", "Tomasz (12)"]
    },
    "interests": ["football", "books", "nature documentaries"],
    "daily_routine": {
      "wake_up": "08:00",
      "lunch": "13:00", 
      "sleep": "22:00"
    },
    "medical": {
      "pain_areas": ["back", "legs"],
      "medications": ["Riluzol"],
      "therapies": ["physiotherapy", "speech therapy"]
    }
  },
  "meta": {
    "created": "2024-08-30T12:00:00Z",
    "last_updated": "2024-08-30T12:00:00Z",
    "version": 1
  }
}
```

**Step 3**: Restart Kompan
```bash
docker restart kompan
```

## File Structure Changes

```
src/
├── context/
│   ├── __init__.py
│   └── user_context.py    # NEW: Simple user context service
├── ai/
│   └── claude_client.py   # MODIFIED: Integrate user context
├── main.py               # MODIFIED: Initialize user context
└── conversation/
    └── manager.py        # MODIFIED: Use personalized prompts

data/
└── user_info.json        # NEW: User information file
```

## Implementation Steps

### Day 1: Basic Context Service
1. Create `src/context/user_context.py`
2. Implement simple JSON loading/saving
3. Add user name and summary methods
4. Test with sample data

### Day 2: Claude Integration  
1. Modify `claude_client.py` to use user context
2. Update system prompts with user information
3. Test personalized conversations
4. Verify fallback to default context

### Day 3: Manual Setup Process
1. Create setup documentation
2. Test manual file creation
3. Verify Docker volume persistence
4. Test restart scenarios

## Future Extensibility (Next Phase)

### Auto-Discovery During Conversations
```python
# Future enhancement - not implemented yet
async def ask_to_remember_info(self, discovered_info: str) -> bool:
    """Ask user if they want to remember discovered information"""
    prompt = f"Odkryłem nową informację: {discovered_info}. Czy chcesz, żebym to zapamiętał?"
    # TTS speaks the question
    # User responds YES/NO
    # If YES, update user_info.json
```

### Conversation Analysis
```python
# Future enhancement - not implemented yet
async def analyze_conversation_for_updates(self, conversation_text: str):
    """Analyze conversation for new user information"""
    # Use Claude to extract new facts about user
    # Ask user for permission to remember
    # Update user_info.json if approved
```

## Benefits of This Approach

1. **Simple**: Just JSON file with user information
2. **Manual Control**: Caregiver provides exactly what they want
3. **No Complexity**: No encryption, no agents, no complex schemas
4. **Immediate Value**: Claude uses real user information right away
5. **Future Ready**: Easy to add auto-discovery later
6. **Privacy**: All data stays local in Docker volume

## Success Criteria

- [ ] Claude uses user's real name in conversations
- [ ] Claude knows about user's family and interests
- [ ] Claude adapts conversation to user's condition
- [ ] System works without user info (fallback)
- [ ] User info persists across restarts
- [ ] Manual setup process is documented and tested

This simplified approach gets personalized conversations working immediately while keeping the door open for future auto-discovery features.
