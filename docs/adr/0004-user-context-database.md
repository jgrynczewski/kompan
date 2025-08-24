# ADR-0004: User Context Database for Personalized Conversations

**Date**: 2024-08-24  
**Status**: Proposed  
**Deciders**: Development Team, User Requirements  

## Context

The application needs to maintain comprehensive user context to enable:
1. **Personalized conversations** - Claude AI needs user background for relevant dialogue
2. **Conversation continuity** - Remember previous topics and preferences across sessions
3. **Caregiver insights** - Provide meaningful summaries with user context
4. **Progressive learning** - Build understanding of user over time
5. **Medical relevance** - Adapt conversations to user's condition and needs

Currently, conversations start fresh each time with no memory of user's personal situation, family, interests, or medical context.

## Decision

Implement a comprehensive user context database system that Claude can read from and automatically update based on conversations.

## Database Schema Design

### Storage Technology: JSON + SQLite Hybrid
- **JSON files** for human-readable user profiles
- **SQLite database** for conversation history and searchable data
- **File-based** for easy backup and portability

### User Context Structure

```json
{
  "user_profile": {
    "personal": {
      "name": "Jan Kowalski",
      "preferred_name": "Janek", 
      "age": 45,
      "gender": "male",
      "condition": "ALS (Stwardnienie zanikowe boczne)",
      "diagnosis_date": "2022-03-15",
      "communication_level": "yes_no_only",
      "cognitive_status": "fully_aware"
    },
    "medical": {
      "mobility": "wheelchair_dependent",
      "pain_areas": ["back", "legs", "neck"],
      "pain_level_usual": 4,
      "medications": [
        {
          "name": "Riluzol",
          "purpose": "ALS progression",
          "schedule": "twice_daily"
        }
      ],
      "last_checkup": "2024-08-10",
      "next_appointment": "2024-09-15",
      "medical_team": {
        "neurologist": "Dr. Maria Nowak",
        "physiotherapist": "Anna Kowal", 
        "speech_therapist": "Piotr Wiśniewski"
      }
    },
    "social": {
      "primary_caregiver": {
        "name": "Maria Kowalska",
        "relationship": "wife",
        "contact": "maria@example.com"
      },
      "family": [
        {
          "name": "Anna Kowalska", 
          "relationship": "daughter",
          "age": 16,
          "notes": "studying for matura exam"
        },
        {
          "name": "Tomasz Kowalski",
          "relationship": "son", 
          "age": 12,
          "notes": "loves football, plays in school team"
        }
      ],
      "friends": [
        {
          "name": "Piotr Zieliński",
          "relationship": "childhood friend",
          "contact_frequency": "weekly"
        }
      ],
      "support_network": [
        "ALS Foundation support group",
        "Local disability advocacy group"
      ]
    },
    "preferences": {
      "topics_of_interest": [
        "family_life",
        "football", 
        "books",
        "nature_documentaries",
        "cooking_shows"
      ],
      "conversation_style": "friendly_informal",
      "sensitive_topics": [
        "work_loss",
        "future_prognosis", 
        "financial_stress"
      ],
      "preferred_times": {
        "morning": "good_mood",
        "afternoon": "often_tired",
        "evening": "family_time"
      },
      "communication_preferences": {
        "pace": "slow_thoughtful",
        "complexity": "simple_direct",
        "humor": "gentle_appropriate"
      }
    },
    "daily_routine": {
      "wake_up": "08:00",
      "morning_routine": "breakfast, medication, physiotherapy", 
      "lunch_time": "13:00",
      "rest_period": "14:00-16:00",
      "family_time": "18:00-20:00",
      "sleep_time": "22:00",
      "therapy_schedule": {
        "monday": "physiotherapy",
        "wednesday": "speech_therapy",
        "friday": "occupational_therapy"
      }
    },
    "conversation_history_summary": {
      "common_topics": ["family", "daily_comfort", "medical_needs"],
      "mood_patterns": {
        "morning": "generally_positive",
        "evening": "sometimes_worried"
      },
      "recurring_concerns": [
        "children's wellbeing",
        "caregiver_burden",
        "maintaining_independence"
      ],
      "positive_topics": [
        "family_achievements", 
        "good_health_days",
        "friend_visits"
      ]
    }
  },
  "metadata": {
    "created": "2024-08-24T10:00:00Z",
    "last_updated": "2024-08-24T15:30:00Z",
    "updated_by": "claude_ai",
    "version": "1.2",
    "backup_count": 5
  }
}
```

## Claude AI Integration

### Context Loading
```python
async def load_user_context(self) -> Dict[str, Any]:
    """Load user context for conversation personalization"""
    context_file = Path("data/user_context.json")
    if context_file.exists():
        with open(context_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return self._create_default_context()

async def inject_context_into_prompt(self, base_prompt: str) -> str:
    """Enhance prompts with user context"""
    context = await self.load_user_context()
    
    context_summary = f"""
    USER CONTEXT:
    Name: {context['user_profile']['personal']['name']}
    Condition: {context['user_profile']['personal']['condition']}
    Family: {', '.join([f["name"] for f in context['user_profile']['social']['family']])}
    Interests: {', '.join(context['user_profile']['preferences']['topics_of_interest'])}
    Recent concerns: {', '.join(context['user_profile']['conversation_history_summary']['recurring_concerns'])}
    """
    
    return f"{context_summary}\n\n{base_prompt}"
```

### Automatic Context Updates
```python
async def update_user_context(self, conversation_data: Dict) -> None:
    """Extract insights from conversation and update user context"""
    
    update_prompt = f"""
    Based on this conversation, identify any new information about the user that should be added to their profile:
    
    CONVERSATION: {conversation_data}
    
    Look for:
    - New family information or updates
    - Medical status changes
    - Mood patterns or concerns
    - New interests or preferences
    - Important life events
    - Changed needs or circumstances
    
    Return a JSON update with only NEW or CHANGED information.
    """
    
    response = await self.client.messages.create(
        model="claude-3-5-sonnet-20241022",
        system="You extract relevant personal information to update user profiles. Only return new/changed information in JSON format.",
        messages=[{"role": "user", "content": update_prompt}]
    )
    
    updates = json.loads(response.content[0].text)
    await self._apply_context_updates(updates)
```

## File Management Strategy

### Directory Structure:
```
data/
├── user_context.json              # Main user profile
├── user_context_backup_1.json     # Automatic backups
├── user_context_backup_2.json
├── conversations/
│   ├── 2024-08-24_sessions.db     # Daily conversation DB
│   └── monthly_summaries/
│       └── 2024-08.json
└── exports/
    └── caregiver_reports/
        └── weekly_2024-08-24.pdf
```

### Backup Strategy:
- Automatic backup before each update
- Daily conversation database snapshots
- Weekly exports for caregivers
- Version control for context changes

## Privacy and Security

### Data Protection:
- Local storage only (no cloud by default)
- Encrypted sensitive medical information
- User consent for data collection
- GDPR compliance considerations

### Access Control:
- Read-only access for conversation engine
- Update permissions for Claude AI insights
- Full access for caregivers with authentication
- Emergency access protocols

## Implementation Plan

### Phase 1: Basic Context System
1. JSON-based user profile storage
2. Context loading in Claude prompts  
3. Manual profile creation interface
4. Basic backup system

### Phase 2: Automatic Updates
1. Conversation analysis for context updates
2. Claude AI integration for profile enhancement
3. Conflict resolution for contradictory information
4. Change logging and approval system

### Phase 3: Advanced Features
1. SQLite integration for searchable history
2. Caregiver dashboard for profile management
3. Export and reporting functionality
4. Machine learning for pattern recognition

## Consequences

### Positive:
- ✅ Highly personalized conversations
- ✅ Continuity across sessions
- ✅ Better caregiver insights
- ✅ Progressive improvement in conversation quality
- ✅ Medical relevance and appropriateness
- ✅ User preference learning

### Negative:
- ❌ Privacy concerns with detailed personal data
- ❌ Complexity in data management
- ❌ Risk of outdated or incorrect information
- ❌ Storage space requirements
- ❌ Backup and security overhead

### Mitigations:
- Comprehensive privacy controls
- User consent and transparency
- Data validation and conflict resolution
- Regular context review with caregivers
- Secure local storage with encryption

## Success Metrics

### Conversation Quality:
- Relevance of topics discussed
- Appropriateness of questions asked
- User engagement levels (measured by response patterns)

### Context Accuracy:
- Accuracy of extracted information
- Frequency of context corrections needed
- Caregiver satisfaction with summaries

### System Reliability:
- Context loading success rate  
- Backup and recovery testing
- Data integrity verification

## Implementation Status

- 🔲 JSON-based user context schema design
- 🔲 Context loading integration with Claude prompts
- 🔲 Automatic context update extraction
- 🔲 Backup and versioning system
- 🔲 Privacy and security implementation
- 🔲 Caregiver management interface

## Related Decisions

- [ADR-0001: Claude API Integration](0001-claude-api-integration.md)
- [ADR-0002: Desktop Application Architecture](0002-desktop-application-architecture.md)
- [ADR-0005: Comprehensive Conversation Logging](#)