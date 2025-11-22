"""
Translation service for the application.
"""
import os
import requests
from typing import Optional, Dict, Any

class TranslateService:
    """Service for handling translations."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """Initialize the translation service.
        
        Args:
            base_url: Base URL of the translation service
        """
        self.base_url = base_url
    
    def translate(self, text: str, target_lang: str, source_lang: str = 'en') -> Optional[str]:
        """Translate text to the target language.
        
        Args:
            text: Text to translate
            target_lang: Target language code (e.g., 'es', 'fr')
            source_lang: Source language code (default: 'en')
            
        Returns:
            Translated text or None if translation fails
        """
        if not text or not target_lang:
            return text
            
        try:
            response = requests.post(
                f"{self.base_url}/translate",
                json={
                    'q': text,
                    'source': source_lang,
                    'target': target_lang,
                    'format': 'text'
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get('translatedText', text)
            return text
        except Exception as e:
            print(f"Translation error: {e}")
            return text

# Create a default instance for easy importing
translate_service = TranslateService()
