import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from context.user_context import UserContext

logger = logging.getLogger(__name__)

@dataclass
class ConversationSession:
    """Represents a conversation session"""
    id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    exchanges: List[Dict[str, Any]] = None
    summary: Optional[str] = None
    
    def __post_init__(self):
        if self.exchanges is None:
            self.exchanges = []

class ConversationManager:
    """Manages conversation flow between Claude engine and TTS"""
    
    def __init__(self, claude_engine, tts_handler, config: Dict[str, Any], user_context: UserContext = None):
        self.claude_engine = claude_engine
        self.tts_handler = tts_handler
        self.config = config
        self.user_context = user_context or UserContext()
        self.current_session: Optional[ConversationSession] = None
        self.conversation_active = False
        
        # Data directory setup
        self.data_dir = Path("/app/data") if Path("/app/data").exists() else Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Offline conversation patterns for fallback
        self.offline_patterns = self._load_offline_patterns()
        self.pattern_index = 0
    
    def _load_offline_patterns(self) -> List[Dict[str, str]]:
        """Load offline conversation patterns for fallback"""
        user_name = self.user_context.get_user_name()
        
        patterns = [
            {
                "question": f"Cześć {user_name}! Czy wszystko u Ciebie w porządku?",
                "yes_followup": f"Cieszę się, że masz dobry dzień, {user_name}. Czy chciałbyś o czymś porozmawiać?",
                "no_followup": f"Przykro mi, że nie czujesz się najlepiej, {user_name}. Czy mogę Ci jakoś pomóc?"
            },
            {
                "question": f"Czy potrzebujesz czegoś od swojego opiekuna, {user_name}?",
                "yes_followup": "Czy to coś pilnego?",
                "no_followup": f"Dobrze, {user_name}. Czy może chciałbyś po prostu porozmawiać?"
            },
            {
                "question": f"Czy masz jakieś dolegliwości, {user_name}?",
                "yes_followup": "Czy to coś, z czym powinieneś skontaktować się z lekarzem?",
                "no_followup": f"To dobrze, że czujesz się komfortowo, {user_name}."
            },
            {
                "question": f"Czy chciałbyś przekazać coś swojej rodzinie, {user_name}?",
                "yes_followup": "Czy to coś ważnego?",
                "no_followup": f"W porządku, {user_name}. Czy może masz ochotę na zwykłą rozmowę?"
            },
            {
                "question": f"Czy jesteś zadowolony z opieki, którą otrzymujesz, {user_name}?",
                "yes_followup": f"To wspaniale, {user_name}. Czy jest coś, za co jesteś szczególnie wdzięczny?",
                "no_followup": "Czy jest coś konkretnego, co mogłoby być lepsze?"
            }
        ]
        return patterns
    
    async def start_conversation(self) -> str:
        """Start a new conversation session"""
        # Create new session
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = ConversationSession(
            id=session_id,
            start_time=datetime.now()
        )
        
        self.conversation_active = True
        self.pattern_index = 0
        
        logger.info(f"Started conversation session: {session_id}")
        
        # Try to use Claude, fallback to offline patterns
        try:
            if self.claude_engine:
                logger.info("Using Claude engine for conversation start")
                question = await self.claude_engine.start_conversation()
                logger.info(f"Claude generated question: {question}")
            else:
                logger.info("No Claude engine, using offline patterns")
                question = self.offline_patterns[0]["question"]
                
            # Log the exchange
            self._log_exchange("system", question, None, "conversation_start")
            
            return question
            
        except Exception as e:
            logger.error(f"Failed to start conversation: {e}", exc_info=True)
            # Use fallback
            question = "Cześć! Jestem Twoim asystentem. Czy masz dobry dzień?"
            self._log_exchange("system", question, None, "conversation_start_fallback")
            return question
    
    async def process_response(self, is_yes: bool) -> Optional[str]:
        """Process user response and generate next question"""
        if not self.conversation_active or not self.current_session:
            logger.warning("No active conversation to process response")
            return None
        
        try:
            # Try to use Claude engine
            if self.claude_engine:
                logger.info(f"Using Claude engine to process response: {'YES' if is_yes else 'NO'}")
                next_question = await self.claude_engine.process_response(is_yes)
                logger.info(f"Claude generated next question: {next_question}")
            else:
                logger.info("No Claude engine, using offline patterns for response")
                next_question = self._get_offline_followup(is_yes)
            
            # Log the exchange
            self._log_exchange("user", None, is_yes, "response")
            if next_question:
                self._log_exchange("system", next_question, None, "question")
            
            # Return the question - don't end conversation prematurely
            return next_question
            
        except Exception as e:
            logger.error(f"Failed to process response: {e}", exc_info=True)
            logger.info("Falling back to offline patterns due to error")
            
            # Try fallback
            next_question = self._get_offline_followup(is_yes)
            if next_question:
                self._log_exchange("system", next_question, None, "question_fallback")
            
            return next_question
    
    def _get_offline_followup(self, is_yes: bool) -> Optional[str]:
        """Get offline followup question"""
        # Use current pattern for followup  
        current_pattern = self.offline_patterns[self.pattern_index % len(self.offline_patterns)]
        followup = current_pattern["yes_followup"] if is_yes else current_pattern["no_followup"]
        
        # Move to next pattern
        self.pattern_index += 1
        
        # Continue conversation for much longer - allow multiple rounds
        if self.pattern_index < len(self.offline_patterns) * 4:  # Allow 4 rounds of patterns
            pattern_idx = self.pattern_index % len(self.offline_patterns) 
            next_pattern = self.offline_patterns[pattern_idx]
            return f"{followup} {next_pattern['question']}"
        else:
            # End conversation after many exchanges
            return None  # Return None to trigger conversation end
    
    def _should_end_conversation(self) -> bool:
        """Determine if conversation should end"""
        if not self.current_session:
            return True
            
        # End after reasonable number of exchanges
        exchange_count = len(self.current_session.exchanges)
        
        # End if too many exchanges (prevent infinite loops)
        if exchange_count > 50:
            return True
        
        # In offline mode, end after going through patterns multiple times
        if not self.claude_engine and self.pattern_index >= len(self.offline_patterns) * 3:
            return True
        
        return False
    
    async def _end_conversation(self):
        """End current conversation session"""
        if not self.current_session:
            return
        
        self.conversation_active = False
        self.current_session.end_time = datetime.now()
        
        # Generate summary
        try:
            if self.claude_engine:
                summary = await self.claude_engine.get_conversation_summary()
            else:
                summary = self._generate_offline_summary()
                
            self.current_session.summary = summary
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            self.current_session.summary = "Błąd podczas generowania podsumowania."
        
        # Save conversation to file
        await self._save_conversation()
        
        logger.info(f"Ended conversation session: {self.current_session.id}")
    
    def _generate_offline_summary(self) -> str:
        """Generate simple offline summary"""
        if not self.current_session:
            return "Brak aktywnej rozmowy."
        
        exchange_count = len(self.current_session.exchanges)
        duration = (self.current_session.end_time - self.current_session.start_time).total_seconds() / 60
        
        yes_responses = sum(1 for ex in self.current_session.exchanges 
                          if ex.get("user_response") is True)
        no_responses = sum(1 for ex in self.current_session.exchanges 
                         if ex.get("user_response") is False)
        
        summary = [
            f"PODSUMOWANIE ROZMOWY",
            f"Data: {self.current_session.start_time.strftime('%Y-%m-%d %H:%M')}",
            f"Czas trwania: {duration:.1f} minut",
            f"Liczba wymian: {exchange_count}",
            f"Odpowiedzi 'tak': {yes_responses}",
            f"Odpowiedzi 'nie': {no_responses}",
            "",
            "Rozmowa przeprowadzona w trybie offline.",
            "Polecana konsultacja z opiekunem w sprawie szczegółów."
        ]
        
        return "\n".join(summary)
    
    def _log_exchange(self, speaker: str, text: Optional[str], response: Optional[bool], exchange_type: str):
        """Log conversation exchange"""
        if not self.current_session:
            return
        
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "text": text,
            "user_response": response,
            "type": exchange_type
        }
        
        self.current_session.exchanges.append(exchange)
    
    async def _save_conversation(self):
        """Save conversation to file"""
        if not self.current_session:
            return
        
        filename = f"conversation_{self.current_session.id}.json"
        filepath = self.data_dir / filename
        
        try:
            conversation_data = {
                "session_id": self.current_session.id,
                "start_time": self.current_session.start_time.isoformat(),
                "end_time": self.current_session.end_time.isoformat() if self.current_session.end_time else None,
                "exchanges": self.current_session.exchanges,
                "summary": self.current_session.summary,
                "config_snapshot": {
                    "language": self.config.get("language", "pl"),
                    "tts_engine": self.config.get("tts_engine", "auto"),
                    "scanning_interval": self.config.get("scanning_interval", 2.0)
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Conversation saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
    
    async def get_summary(self) -> str:
        """Get current conversation summary"""
        if not self.current_session:
            return "Brak aktywnej rozmowy."
        
        if self.current_session.summary:
            return self.current_session.summary
        
        # Generate summary for active conversation
        try:
            if self.claude_engine:
                summary = await self.claude_engine.get_conversation_summary()
            else:
                summary = self._generate_offline_summary()
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            return "Błąd podczas generowania podsumowania."
    
    async def reset(self):
        """Reset conversation manager"""
        if self.current_session and self.conversation_active:
            await self._end_conversation()
        
        self.current_session = None
        self.conversation_active = False
        self.pattern_index = 0
        
        if self.claude_engine:
            # Reset Claude engine state
            self.claude_engine.conversation_history = []
            self.claude_engine.current_question = None
        
        logger.info("Conversation manager reset")
    
    def get_conversation_status(self) -> Dict[str, Any]:
        """Get current conversation status"""
        status = {
            "active": self.conversation_active,
            "session_id": self.current_session.id if self.current_session else None,
            "exchange_count": len(self.current_session.exchanges) if self.current_session else 0,
            "start_time": self.current_session.start_time.isoformat() if self.current_session else None,
            "claude_available": self.claude_engine is not None,
            "tts_available": self.tts_handler is not None
        }
        
        return status
    
    async def load_conversation_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Load recent conversation history"""
        history = []
        
        try:
            for file_path in self.data_dir.glob("conversation_*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        conversation_data = json.load(f)
                    
                    # Check if within date range
                    start_time = datetime.fromisoformat(conversation_data["start_time"])
                    if (datetime.now() - start_time).days <= days:
                        history.append(conversation_data)
                        
                except Exception as e:
                    logger.warning(f"Failed to load conversation file {file_path}: {e}")
            
            # Sort by start time (newest first)
            history.sort(key=lambda x: x["start_time"], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to load conversation history: {e}")
        
        return history