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
