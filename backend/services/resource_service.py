"""
Resource service for managing disaster response resources.
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

class ResourceService:
    """Service for managing disaster response resources."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the resource service.
        
        Args:
            data_dir: Directory containing resource data files
        """
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
        self.data_dir = data_dir
    
    def get_all_resources(self) -> List[Dict]:
        """Get all available resources.
        
        Returns:
            List of resource dictionaries
        """
        resources = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json'):
                with open(os.path.join(self.data_dir, filename), 'r', encoding='utf-8') as f:
                    resources.extend(json.load(f))
        return resources
    
    def find_resources_by_keyword(self, keyword: str) -> List[Dict]:
        """Find resources matching the given keyword.
        
        Args:
            keyword: Keyword to search for in resource titles and descriptions
            
        Returns:
            List of matching resource dictionaries
        """
        keyword = keyword.lower()
        all_resources = self.get_all_resources()
        return [
            r for r in all_resources
            if (keyword in r.get('title', '').lower() or 
                 keyword in r.get('description', '').lower() or
                 any(keyword in tag.lower() for tag in r.get('tags', [])))
        ]

# Create a default instance for easy importing
resource_service = ResourceService()
