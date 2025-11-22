# This file makes the backend directory a Python package
# Import all services to make them available when importing from backend.services
from .resource_service import ResourceService, resource_service
from .template_service import TemplateService, template_service
from .translate_service import TranslateService, translate_service
from .sos_service import SOSService

# Define __all__ for explicit exports
__all__ = [
    'ResourceService',
    'resource_service',
    'TemplateService',
    'template_service',
    'TranslateService',
    'translate_service',
    'SOSService'
]