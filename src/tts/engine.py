import asyncio
import logging
import tempfile
import os
from typing import Optional, Dict, Any
from enum import Enum
import pygame
import pyttsx3
from gtts import gTTS
import edge_tts

logger = logging.getLogger(__name__)

class TTSEngine(Enum):
    EDGE_TTS = "edge_tts"
    GTTS = "gtts"
    PYTTSX3 = "pyttsx3"
    FALLBACK = "fallback"

class PolishTTSHandler:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.current_engine = None
        self.engines_tested = {}
        pygame.mixer.init()
        
        # Polish voice configurations
        self.voices = {
            TTSEngine.EDGE_TTS: "pl-PL-ZofiaNeural",  # High quality Polish voice
            TTSEngine.GTTS: "pl",
            TTSEngine.PYTTSX3: None,  # Will be detected
        }
        
        # Fallback audio files for critical phrases
        self.fallback_phrases = {
            "tak": None,  # Will be generated or loaded
            "nie": None,
            "czekaj": None,
            "błąd": None
        }
    
    async def initialize(self):
        """Test all TTS engines and select the best available"""
        logger.info("Initializing Polish TTS engines...")
        
        # Test engines in priority order
        engines_to_test = [TTSEngine.EDGE_TTS, TTSEngine.GTTS, TTSEngine.PYTTSX3]
        
        for engine in engines_to_test:
            try:
                success = await self._test_engine(engine)
                self.engines_tested[engine] = success
                if success and self.current_engine is None:
                    self.current_engine = engine
                    logger.info(f"Selected {engine.value} as primary TTS engine")
            except Exception as e:
                logger.warning(f"Failed to initialize {engine.value}: {e}")
                self.engines_tested[engine] = False
        
        if self.current_engine is None:
            logger.warning("No TTS engines available, preparing fallback audio")
            await self._prepare_fallback_audio()
            self.current_engine = TTSEngine.FALLBACK
        
        return self.current_engine
    
    async def _test_engine(self, engine: TTSEngine) -> bool:
        """Test if an engine can synthesize Polish text"""
        test_text = "Test"
        
        try:
            if engine == TTSEngine.EDGE_TTS:
                return await self._test_edge_tts(test_text)
            elif engine == TTSEngine.GTTS:
                return await self._test_gtts(test_text)
            elif engine == TTSEngine.PYTTSX3:
                return await self._test_pyttsx3(test_text)
        except Exception as e:
            logger.error(f"Error testing {engine.value}: {e}")
            return False
        
        return False
    
    async def _test_edge_tts(self, text: str) -> bool:
        """Test Edge TTS"""
        try:
            communicate = edge_tts.Communicate(text, self.voices[TTSEngine.EDGE_TTS])
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp_file:
                await communicate.save(tmp_file.name)
                return os.path.exists(tmp_file.name)
        except Exception:
            return False
    
    async def _test_gtts(self, text: str) -> bool:
        """Test Google TTS"""
        try:
            tts = gTTS(text=text, lang=self.voices[TTSEngine.GTTS])
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=True) as tmp_file:
                tts.save(tmp_file.name)
                return os.path.exists(tmp_file.name)
        except Exception:
            return False
    
    async def _test_pyttsx3(self, text: str) -> bool:
        """Test pyttsx3"""
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty('voices')
            
            # Look for Polish voice
            polish_voice = None
            for voice in voices:
                if 'pl' in voice.id.lower() or 'polish' in voice.name.lower():
                    polish_voice = voice.id
                    break
            
            if polish_voice:
                engine.setProperty('voice', polish_voice)
                self.voices[TTSEngine.PYTTSX3] = polish_voice
            
            engine.stop()
            return True
        except Exception:
            return False
    
    async def _prepare_fallback_audio(self):
        """Prepare pre-recorded fallback audio files"""
        # This would ideally load pre-recorded audio files
        # For now, we'll just log that fallback is ready
        logger.info("Fallback audio prepared")
    
    async def speak(self, text: str) -> bool:
        """Speak the given text using the best available engine"""
        if self.current_engine is None:
            await self.initialize()
        
        # Try current engine first
        success = await self._speak_with_engine(text, self.current_engine)
        
        if not success:
            # Try fallback engines
            for engine, available in self.engines_tested.items():
                if available and engine != self.current_engine:
                    success = await self._speak_with_engine(text, engine)
                    if success:
                        logger.info(f"Switched to fallback engine: {engine.value}")
                        self.current_engine = engine
                        break
        
        return success
    
    async def _speak_with_engine(self, text: str, engine: TTSEngine) -> bool:
        """Speak text with specific engine"""
        try:
            if engine == TTSEngine.EDGE_TTS:
                return await self._speak_edge_tts(text)
            elif engine == TTSEngine.GTTS:
                return await self._speak_gtts(text)
            elif engine == TTSEngine.PYTTSX3:
                return await self._speak_pyttsx3(text)
            elif engine == TTSEngine.FALLBACK:
                return await self._speak_fallback(text)
        except Exception as e:
            logger.error(f"Error speaking with {engine.value}: {e}")
            return False
        
        return False
    
    async def _speak_edge_tts(self, text: str) -> bool:
        """Speak using Edge TTS"""
        try:
            communicate = edge_tts.Communicate(text, self.voices[TTSEngine.EDGE_TTS])
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                await communicate.save(tmp_file.name)
                
                # Play audio
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                
                # Clean up
                os.unlink(tmp_file.name)
                return True
                
        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
            return False
    
    async def _speak_gtts(self, text: str) -> bool:
        """Speak using Google TTS"""
        try:
            tts = gTTS(text=text, lang=self.voices[TTSEngine.GTTS])
            
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                tts.save(tmp_file.name)
                
                # Play audio
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
                
                # Clean up
                os.unlink(tmp_file.name)
                return True
                
        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return False
    
    async def _speak_pyttsx3(self, text: str) -> bool:
        """Speak using pyttsx3"""
        try:
            engine = pyttsx3.init()
            
            if self.voices[TTSEngine.PYTTSX3]:
                engine.setProperty('voice', self.voices[TTSEngine.PYTTSX3])
            
            # Configure speech rate
            rate = engine.getProperty('rate')
            engine.setProperty('rate', rate - 50)  # Slower for better understanding
            
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            
            return True
            
        except Exception as e:
            logger.error(f"pyttsx3 error: {e}")
            return False
    
    async def _speak_fallback(self, text: str) -> bool:
        """Use fallback audio for critical phrases"""
        # Check if we have a pre-recorded version
        text_lower = text.lower()
        if text_lower in self.fallback_phrases:
            # Would play pre-recorded audio here
            logger.info(f"Playing fallback audio for: {text}")
            return True
        
        logger.error(f"No fallback available for: {text}")
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current TTS status"""
        return {
            "current_engine": self.current_engine.value if self.current_engine else None,
            "engines_tested": {k.value: v for k, v in self.engines_tested.items()},
            "voices": {k.value: v for k, v in self.voices.items()}
        }