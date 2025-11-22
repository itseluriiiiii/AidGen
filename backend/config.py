"""
Configuration settings for the AidGen application.
Loads environment variables and provides configuration settings.
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file (always relative to project root)
BASE_DIR = Path(__file__).resolve().parents[1]
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Base configuration class."""
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Vonage SMS Configuration
    VONAGE_API_URL = os.getenv('VONAGE_API_URL', 'https://rest.nexmo.com/sms/json')
    VONAGE_API_KEY = os.getenv('VONAGE_API_KEY')
    VONAGE_API_SECRET = os.getenv('VONAGE_API_SECRET')
    VONAGE_FROM_NUMBER = os.getenv('VONAGE_FROM_NUMBER')

    # SOS contact configuration (format: "Name:+1234567890,Another:+1987654321")
    SOS_EMERGENCY_CONTACTS = os.getenv('SOS_EMERGENCY_CONTACTS', '')

    @classmethod
    def _has_sos_contacts(cls) -> bool:
        for raw in (cls.SOS_EMERGENCY_CONTACTS or '').split(','):
            if ':' not in raw:
                continue
            _, phone = raw.split(':', 1)
            if phone.strip():
                return True
        return False

    @classmethod
    def validate_config(cls):
        """Validate that all required configurations are set."""
        required_vars = [
            'VONAGE_API_KEY',
            'VONAGE_API_SECRET',
            'VONAGE_FROM_NUMBER'
        ]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        if not cls._has_sos_contacts():
            missing_vars.append('SOS_EMERGENCY_CONTACTS')
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

# Initialize and validate config
config = Config()
try:
    config.validate_config()
except ValueError as e:
    import warnings
    warnings.warn(str(e))
