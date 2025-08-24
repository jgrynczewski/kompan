import asyncio
import logging
from typing import Optional, Dict, List, Any
from anthropic import AsyncAnthropic
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ClaudeConversationEngine:
    def __init__(self, api_key: str, config: Dict[str, Any]):
        self.client = AsyncAnthropic(
            api_key=api_key,
            timeout=config.get("api_timeout", 10)
        )
        self.config = config
        self.conversation_history: List[Dict[str, str]] = []
        self.user_context = {
            "preferences": {},
            "personal_info": {},
            "conversation_topics": [],
            "mood_indicators": []
        }
        self.current_question = None
        self.question_context = {}
        
        # Polish system prompt for natural conversation
        self.system_prompt = """
        Jesteś asystentem komunikacyjnym dla osoby z poważnymi niepełnosprawnościami fizycznymi.
        
        WAŻNE ZASADY:
        1. Osoba może odpowiadać TYLKO TAK lub NIE
        2. Prowadzisz całą rozmowę - musisz wydedukować co osoba chce przekazać
        3. Zadawaj pytania tak, by krok po kroku zrozumieć jej myśli i potrzeby
        4. Bądź cierpliwy, empatyczny i naturalny
        5. Pamiętaj wszystkie wcześniejsze odpowiedzi w rozmowie
        6. Podsumowuj ustalenia, by osoba mogła je przekazać opiekunowi
        
        CELE ROZMOWY:
        - Zapewnić towarzystwo i możliwość wyrażenia myśli
        - Pomóc w komunikowaniu potrzeb i uczuć
        - Być przyjacielem dla osoby, która rzadko rozmawia
        - Zapisać ważne informacje dla opiekunów
        
        STYL:
        - Mów naturalnie, jak przyjaciel
        - Używaj prostych, jasnych pytań
        - Pozwól osobie prowadzić tematy rozmowy
        - Bądź cierpliwy w dedukcji znaczenia
        
        Zawsze odpowiadaj w języku polskim i zadawaj tylko jedno pytanie na raz.
        """
    
    async def start_conversation(self) -> str:
        """Start a new conversation using Claude API"""
        self.conversation_history = []
        self.current_question = None
        
        # Choose appropriate greeting based on time
        hour = datetime.now().hour
        if hour < 12:
            greeting = "Dzień dobry!"
        elif hour < 18:
            greeting = "Dzień dobry!"
        else:
            greeting = "Dobry wieczór!"
        
        # Use Claude API to generate personalized opening
        try:
            prompt = f"""
            {greeting} Jestem asystentem komunikacyjnym dla osoby z niepełnosprawnością, która może odpowiadać tylko TAK lub NIE.
            
            Rozpocznij naturalną, ciepłą rozmowę. Wygeneruj pierwsze pytanie, które:
            1. Jest przyjazne i osobiste, jak rozmowa z przyjacielem
            2. Pozwala osobie wyrazić swoje obecne samopoczucie
            3. Można na nie odpowiedzieć TAK lub NIE
            4. Nie brzmi jak ankieta medyczna
            5. Jest konkretne i angażujące
            
            Przykłady dobrych pytań:
            - "Czy dzisiaj czujesz się lepiej niż wczoraj?"
            - "Czy miałeś przyjemny sen?"
            - "Czy cieszyś się z dzisiejszego dnia?"
            
            Odpowiedz TYLKO pytaniem, bez dodatkowych komentarzy.
            """
            
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=150,
                temperature=0.8,
                system=self.system_prompt,
                messages=[{
                    "role": "user", 
                    "content": prompt
                }]
            )
            
            initial_question = response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate opening with Claude API: {e}")
            # Fallback to more natural static question
            initial_question = f"{greeting} Czy czujesz się dzisiaj dobrze?"
        
        self.current_question = initial_question
        self.question_context = {
            "type": "greeting",
            "topic": "daily_wellbeing", 
            "expecting": "general_mood"
        }
        
        logger.info("Started new conversation")
        return initial_question
    
    async def process_response(self, is_yes: bool) -> str:
        """Process yes/no response and generate next question"""
        if self.current_question is None:
            return await self.start_conversation()
        
        # Record the response
        response_text = "tak" if is_yes else "nie"
        self.conversation_history.append({
            "question": self.current_question,
            "response": response_text,
            "timestamp": datetime.now().isoformat(),
            "context": self.question_context.copy()
        })
        
        # Update user context based on response
        self._update_user_context(is_yes)
        
        # Generate next question
        try:
            next_question = await self._generate_next_question(is_yes)
            self.current_question = next_question
            return next_question
            
        except Exception as e:
            logger.error(f"Error generating question: {e}")
            return await self._get_fallback_question(is_yes)
    
    def _update_user_context(self, is_yes: bool):
        """Update user context based on response"""
        context_type = self.question_context.get("type", "")
        topic = self.question_context.get("topic", "")
        
        if context_type == "greeting":
            self.user_context["mood_indicators"].append({
                "timestamp": datetime.now().isoformat(),
                "indicator": "good_day" if is_yes else "difficult_day"
            })
        
        # Track conversation topics
        if topic and topic not in self.user_context["conversation_topics"]:
            self.user_context["conversation_topics"].append(topic)
    
    async def _generate_next_question(self, is_yes: bool) -> str:
        """Generate next question using Claude API"""
        
        # Build conversation context for Claude
        conversation_context = self._build_conversation_context()
        
        prompt = f"""
        KONTEKST ROZMOWY:
        {conversation_context}
        
        OSTATNIA ODPOWIEDŹ: {"TAK" if is_yes else "NIE"}
        
        Jako asystent komunikacyjny, wygeneruj następne naturalne pytanie, które:
        1. Kontynuuje rozmowę w logiczny sposób
        2. Pomaga lepiej zrozumieć osobę i jej potrzeby
        3. Jest przyjazne i wspierające
        4. Może być odpowiedziane TAK lub NIE
        
        Odpowiedz TYLKO pytaniem, bez dodatkowych komentarzy.
        """
        
        try:
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=200,
                temperature=0.7,
                system=self.system_prompt,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            question = response.content[0].text.strip()
            
            # Update question context based on generated question
            self._analyze_question_context(question)
            
            return question
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    def _build_conversation_context(self) -> str:
        """Build conversation context for Claude"""
        context_parts = []
        
        # Recent conversation history (last 5 exchanges)
        recent_history = self.conversation_history[-5:]
        if recent_history:
            context_parts.append("OSTATNIE PYTANIA I ODPOWIEDZI:")
            for entry in recent_history:
                context_parts.append(f"P: {entry['question']}")
                context_parts.append(f"O: {entry['response']}")
            context_parts.append("")
        
        # User context
        if self.user_context["mood_indicators"]:
            latest_mood = self.user_context["mood_indicators"][-1]
            context_parts.append(f"NASTRÓJ: {latest_mood['indicator']}")
        
        if self.user_context["conversation_topics"]:
            topics = ", ".join(self.user_context["conversation_topics"][-3:])  # Last 3 topics
            context_parts.append(f"OSTATNIE TEMATY: {topics}")
        
        return "\n".join(context_parts)
    
    def _analyze_question_context(self, question: str):
        """Analyze generated question and set context"""
        question_lower = question.lower()
        
        # Detect question type and topic
        if any(word in question_lower for word in ["czujesz", "nastrój", "samopoczucie"]):
            self.question_context = {"type": "emotion", "topic": "feelings"}
        elif any(word in question_lower for word in ["chciałbyś", "potrzebujesz", "pragnieszs"]):
            self.question_context = {"type": "needs", "topic": "desires"}
        elif any(word in question_lower for word in ["rodzina", "bliscy", "opiekun"]):
            self.question_context = {"type": "relationships", "topic": "family"}
        elif any(word in question_lower for word in ["jedzenie", "jeść", "pić"]):
            self.question_context = {"type": "physical_needs", "topic": "food_drink"}
        elif any(word in question_lower for word in ["ból", "boli", "dolegliwości"]):
            self.question_context = {"type": "physical_needs", "topic": "pain_discomfort"}
        else:
            self.question_context = {"type": "general", "topic": "conversation"}
    
    async def _get_fallback_question(self, is_yes: bool) -> str:
        """Get fallback question when API fails"""
        fallback_questions = [
            "Czy wszystko u Ciebie w porządku?",
            "Czy potrzebujesz czegoś od swojego opiekuna?",
            "Czy chciałbyś o czymś opowiedzieć?",
            "Czy coś Cię martwi?",
            "Czy masz jakieś potrzeby, z którymi mogę pomóc?"
        ]
        
        # Simple logic based on conversation length
        question_index = min(len(self.conversation_history), len(fallback_questions) - 1)
        question = fallback_questions[question_index]
        
        self.question_context = {"type": "fallback", "topic": "general"}
        return question
    
    async def get_conversation_summary(self) -> str:
        """Generate conversation summary for caregivers"""
        if not self.conversation_history:
            return "Rozmowa nie została rozpoczęta."
        
        # Build summary context
        summary_context = []
        summary_context.append(f"DATA ROZMOWY: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        summary_context.append(f"DŁUGOŚĆ ROZMOWY: {len(self.conversation_history)} wymian")
        summary_context.append("")
        
        # Add conversation highlights
        summary_context.append("PRZEBIEG ROZMOWY:")
        for i, entry in enumerate(self.conversation_history[-10:], 1):  # Last 10 exchanges
            summary_context.append(f"{i}. {entry['question']} → {entry['response']}")
        
        try:
            prompt = f"""
            Przygotuj zwięzłe podsumowanie rozmowy dla opiekuna osoby niepełnosprawnej.
            
            {chr(10).join(summary_context)}
            
            PODSUMOWANIE POWINNO ZAWIERAĆ:
            1. Ogólny nastrój i samopoczucie osoby
            2. Główne tematy rozmowy
            3. Zidentyfikowane potrzeby lub problemy
            4. Zalecenia dla opiekuna
            
            Bądź konkretny i pomocny dla opiekuna.
            """
            
            response = await self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=400,
                temperature=0.5,
                system="Jesteś asystentem przygotowującym podsumowania rozmów dla opiekunów osób niepełnosprawnych.",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return self._generate_simple_summary()
    
    def _generate_simple_summary(self) -> str:
        """Generate simple summary without API"""
        if not self.conversation_history:
            return "Brak rozmowy do podsumowania."
        
        yes_count = sum(1 for entry in self.conversation_history if entry['response'] == 'tak')
        no_count = len(self.conversation_history) - yes_count
        
        summary = []
        summary.append(f"PODSUMOWANIE ROZMOWY - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        summary.append(f"Długość rozmowy: {len(self.conversation_history)} pytań")
        summary.append(f"Odpowiedzi pozytywne: {yes_count}, negatywne: {no_count}")
        summary.append("")
        
        # Identify main topics
        topics = self.user_context.get("conversation_topics", [])
        if topics:
            summary.append(f"Główne tematy: {', '.join(topics[-5:])}")
        
        # Mood indicators
        mood_indicators = self.user_context.get("mood_indicators", [])
        if mood_indicators:
            latest_mood = mood_indicators[-1]['indicator']
            summary.append(f"Nastrój: {latest_mood}")
        
        return "\n".join(summary)
    
    def get_conversation_data(self) -> Dict[str, Any]:
        """Get complete conversation data for logging"""
        return {
            "conversation_history": self.conversation_history,
            "user_context": self.user_context,
            "start_time": self.conversation_history[0]["timestamp"] if self.conversation_history else None,
            "end_time": datetime.now().isoformat(),
            "total_exchanges": len(self.conversation_history)
        }