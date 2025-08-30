import asyncio
import json
import logging
import os
import webbrowser
from pathlib import Path
from typing import Dict, Any, Optional
import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from tts.engine import PolishTTSHandler
from ai.claude_client import ClaudeConversationEngine
from conversation.manager import ConversationManager
from context.user_context import UserContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class KompanApp:
    def __init__(self):
        self.app = FastAPI(title="Kompan", description="AI Communication Assistant")
        self.config = self.load_config()
        self.user_context: Optional[UserContext] = None
        self.tts_handler: Optional[PolishTTSHandler] = None
        self.claude_engine: Optional[ClaudeConversationEngine] = None
        self.conversation_manager: Optional[ConversationManager] = None
        self.active_connections: list[WebSocket] = []
        
        self.setup_app()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        config_path = Path("/app/config/settings.json")
        if not config_path.exists():
            config_path = Path("config/settings.json")
        
        try:
            with open(config_path) as f:
                config = json.load(f)
                
            # Get Claude API key from environment if not in config
            if not config.get("claude_api_key"):
                config["claude_api_key"] = os.getenv("CLAUDE_API_KEY", "")
                
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            # Return default config
            return {
                "scanning_interval": 2.0,
                "tts_engine": "auto",
                "language": "pl",
                "api_timeout": 10,
                "conversation_history_days": 30,
                "claude_api_key": os.getenv("CLAUDE_API_KEY", ""),
                "gui_port": 8080,
                "api_port": 8081,
                "audio_device": "default"
            }
    
    def setup_app(self):
        """Setup FastAPI application"""
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Serve static files (GUI)
        self.app.mount("/static", StaticFiles(directory="src/gui"), name="static")
        
        # Routes
        self.setup_routes()
        
        # Initialize components on startup
        self.app.add_event_handler("startup", self.startup)
        self.app.add_event_handler("shutdown", self.shutdown)
    
    def setup_routes(self):
        """Setup API routes"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def serve_gui():
            """Serve main GUI"""
            gui_path = Path("src/gui/index.html")
            if gui_path.exists():
                with open(gui_path) as f:
                    return HTMLResponse(f.read())
            return HTMLResponse("<h1>Kompan - GUI not found</h1>")
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {"status": "healthy", "timestamp": asyncio.get_event_loop().time()}
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time communication"""
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    await self.handle_websocket_message(websocket, json.loads(data))
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
                logger.info("WebSocket client disconnected")
        
        # API Routes
        @self.app.get("/api/settings")
        async def get_settings():
            """Get current settings"""
            return self.config
        
        @self.app.post("/api/settings")
        async def update_settings(settings: dict):
            """Update settings"""
            self.config.update(settings)
            await self.save_config()
            return {"success": True}
        
        @self.app.post("/api/tts/initialize")
        async def initialize_tts():
            """Initialize TTS engine"""
            try:
                if not self.tts_handler:
                    self.tts_handler = PolishTTSHandler(self.config)
                
                engine = await self.tts_handler.initialize()
                return {"success": True, "engine": engine.value if engine else "none"}
            except Exception as e:
                logger.error(f"TTS initialization failed: {e}")
                return {"success": False, "error": str(e)}
        
        @self.app.post("/api/tts/speak")
        async def speak_text(request: dict):
            """Speak text using TTS"""
            text = request.get("text", "")
            if not text:
                raise HTTPException(status_code=400, detail="No text provided")
            
            if not self.tts_handler:
                raise HTTPException(status_code=500, detail="TTS not initialized")
            
            success = await self.tts_handler.speak(text)
            return {"success": success}
        
        @self.app.get("/api/tts/status")
        async def get_tts_status():
            """Get TTS engine status"""
            if not self.tts_handler:
                return {"status": "not_initialized"}
            
            return self.tts_handler.get_status()
        
        @self.app.post("/api/conversation/start")
        async def start_conversation():
            """Start new conversation"""
            if not self.conversation_manager:
                raise HTTPException(status_code=500, detail="Conversation manager not initialized")
            
            question = await self.conversation_manager.start_conversation()
            return {"question": question}
        
        @self.app.post("/api/respond")
        async def respond(request: dict):
            """Process yes/no response with robust error handling"""
            try:
                response = request.get("response")
                if response is None:
                    raise HTTPException(status_code=400, detail="No response provided")
                
                if not self.conversation_manager:
                    logger.error("Conversation manager not initialized")
                    return {"question": "Przepraszam, wystąpił problem. Czy chciałbyś rozpocząć nową rozmowę?", "error": True}
                
                next_question = await self.conversation_manager.process_response(response)
                
                if next_question is None:
                    # Conversation ended normally
                    return {"question": None, "ended": True, "summary": "Rozmowa zakończona"}
                
                return {"question": next_question, "success": True}
                
            except Exception as e:
                logger.error(f"Error processing response: {e}")
                # Return a safe fallback question instead of crashing
                return {
                    "question": "Wystąpił problem. Czy wszystko u Ciebie w porządku?", 
                    "error": True,
                    "message": "Błąd podczas przetwarzania odpowiedzi"
                }
        
        @self.app.get("/api/conversation/summary")
        async def get_conversation_summary():
            """Get conversation summary"""
            if not self.conversation_manager:
                raise HTTPException(status_code=500, detail="Conversation manager not initialized")
            
            summary = await self.conversation_manager.get_summary()
            return {"summary": summary}
        
        @self.app.post("/api/conversation/reset")
        async def reset_conversation():
            """Reset conversation"""
            if not self.conversation_manager:
                raise HTTPException(status_code=500, detail="Conversation manager not initialized")
            
            await self.conversation_manager.reset()
            return {"success": True}
    
    async def handle_websocket_message(self, websocket: WebSocket, data: dict):
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")
        
        try:
            if message_type == "start_conversation":
                await self.ws_start_conversation(websocket)
            elif message_type == "response":
                await self.ws_process_response(websocket, data.get("value"))
            elif message_type == "audio_cue":
                await self.ws_play_audio_cue(websocket, data.get("text"))
            elif message_type == "restart":
                await self.ws_restart_conversation(websocket)
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }))
        except Exception as e:
            logger.error(f"WebSocket message handling error: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": str(e)
            }))
    
    async def ws_start_conversation(self, websocket: WebSocket):
        """Start conversation via WebSocket"""
        if not self.conversation_manager:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Conversation manager not initialized"
            }))
            return
        
        question = await self.conversation_manager.start_conversation()
        
        # Send question to client
        await websocket.send_text(json.dumps({
            "type": "question",
            "text": question
        }))
        
        # Start TTS
        await self.speak_and_notify(question, websocket)
    
    async def ws_process_response(self, websocket: WebSocket, response: bool):
        """Process response via WebSocket with robust error handling"""
        try:
            if not self.conversation_manager:
                await websocket.send_text(json.dumps({
                    "type": "question",
                    "text": "Przepraszam, wystąpił problem. Czy chciałbyś rozpocząć nową rozmowę?",
                    "error": True
                }))
                return
            
            next_question = await self.conversation_manager.process_response(response)
            
            if next_question:
                # Send next question
                await websocket.send_text(json.dumps({
                    "type": "question",
                    "text": next_question
                }))
                
                # Start TTS
                await self.speak_and_notify(next_question, websocket)
            else:
                # Conversation ended
                try:
                    summary = await self.conversation_manager.get_summary()
                except:
                    summary = "Rozmowa zakończona"
                
                await websocket.send_text(json.dumps({
                    "type": "conversation_end",
                    "summary": summary
                }))
                
        except Exception as e:
            logger.error(f"Error processing WebSocket response: {e}")
            # Send fallback question instead of crashing
            await websocket.send_text(json.dumps({
                "type": "question",
                "text": "Wystąpił problem. Czy wszystko u Ciebie w porządku?",
                "error": True
            }))
    
    async def ws_play_audio_cue(self, websocket: WebSocket, text: str):
        """Play audio cue via WebSocket"""
        if self.tts_handler and text:
            await self.tts_handler.speak(text)
    
    async def ws_restart_conversation(self, websocket: WebSocket):
        """Restart conversation via WebSocket"""
        if self.conversation_manager:
            await self.conversation_manager.reset()
        await self.ws_start_conversation(websocket)
    
    async def speak_and_notify(self, text: str, websocket: WebSocket):
        """Speak text and notify client about TTS state"""
        if not self.tts_handler:
            return
        
        # Notify TTS start
        await websocket.send_text(json.dumps({
            "type": "tts_start"
        }))
        
        # Speak text
        success = await self.tts_handler.speak(text)
        
        # Notify TTS end
        await websocket.send_text(json.dumps({
            "type": "tts_end"
        }))
        
        if not success:
            await websocket.send_text(json.dumps({
                "type": "status",
                "message": "Błąd TTS",
                "level": "error"
            }))
    
    async def save_config(self):
        """Save configuration to file"""
        config_path = Path("/app/config/settings.json")
        if not config_path.exists():
            config_path = Path("config/settings.json")
        
        try:
            with open(config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    async def startup(self):
        """Startup initialization"""
        logger.info("Starting Kompan application...")
        
        # Initialize user context
        try:
            self.user_context = UserContext()
            logger.info("User context initialized")
        except Exception as e:
            logger.error(f"Failed to initialize user context: {e}")
        
        # Initialize TTS
        try:
            self.tts_handler = PolishTTSHandler(self.config)
            await self.tts_handler.initialize()
            logger.info("TTS handler initialized")
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
        
        # Initialize Claude engine
        if self.config.get("claude_api_key"):
            try:
                self.claude_engine = ClaudeConversationEngine(
                    self.config["claude_api_key"], 
                    self.config,
                    self.user_context
                )
                logger.info("Claude engine initialized with user context")
            except Exception as e:
                logger.error(f"Failed to initialize Claude: {e}")
        else:
            logger.warning("No Claude API key provided")
        
        # Initialize conversation manager
        try:
            self.conversation_manager = ConversationManager(
                self.claude_engine,
                self.tts_handler,
                self.config,
                self.user_context
            )
            logger.info("Conversation manager initialized with user context")
        except Exception as e:
            logger.error(f"Failed to initialize conversation manager: {e}")
        
        logger.info("Kompan application started successfully")
        
        # Auto-open browser if not in container
        if not os.getenv("DOCKER_ENV"):
            webbrowser.open(f"http://localhost:{self.config['gui_port']}")
    
    async def shutdown(self):
        """Shutdown cleanup"""
        logger.info("Shutting down Kompan application...")
        
        # Close WebSocket connections
        for connection in self.active_connections:
            try:
                await connection.close()
            except:
                pass
        
        logger.info("Kompan application shut down")

# Create application instance
kompan = KompanApp()
app = kompan.app

def main():
    """Main entry point"""
    config = kompan.config
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config["gui_port"],
        reload=False,
        access_log=False
    )

if __name__ == "__main__":
    main()