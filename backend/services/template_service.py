"""
Template service for managing message templates.
"""
import os
import json
from pathlib import Path
from typing import Dict, Optional, Any

class TemplateService:
    """Service for managing message templates."""
    
    def __init__(self, templates_dir: str = None):
        """Initialize the template service.
        
        Args:
            templates_dir: Directory containing template files
        """
        if templates_dir is None:
            templates_dir = os.path.join(
                os.path.dirname(__file__), '..', 'templates'
            )
        self.templates_dir = templates_dir
        self._ensure_templates_dir()
    
    def _ensure_templates_dir(self):
        """Ensure the templates directory exists."""
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def load_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Load a template by name.
        
        Args:
            template_name: Name of the template to load
            
        Returns:
            Template data as a dictionary, or None if not found
        """
        template_path = os.path.join(
            self.templates_dir, f"{template_name}.json"
        )
        
        if not os.path.exists(template_path):
            return None
            
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading template {template_name}: {e}")
            return None
    
    def save_template(self, template_name: str, template_data: Dict[str, Any]) -> bool:
        """Save a template.
        
        Args:
            template_name: Name of the template to save
            template_data: Template data as a dictionary
            
        Returns:
            True if successful, False otherwise
        """
        template_path = os.path.join(
            self.templates_dir, f"{template_name}.json"
        )
        
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving template {template_name}: {e}")
            return False

# Create a default instance for easy importing
template_service = TemplateService()
