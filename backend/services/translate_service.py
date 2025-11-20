# backend/services/translate_service.py
import os
from pathlib import Path
try:
    import argostranslate.package
    import argostranslate.translate
except Exception:
    argostranslate = None

DATA_DIR = Path(__file__).resolve().parents[1] / "offline_data"
ARGOS_DIR = DATA_DIR / "argos_models"

def install_argos_model(path: str):
    if argostranslate is None:
        raise RuntimeError("argostranslate not installed")
    package_path = Path(path)
    argostranslate.package.install_from_path(str(package_path))

def ensure_models_installed():
    if argostranslate is None:
        return False
    if not ARGOS_DIR.exists():
        return False
    for p in ARGOS_DIR.glob("*.argosmodel"):
        try:
            install_argos_model(str(p))
        except Exception:
            pass
    return True

def translate_text(text: str, from_code="en", to_code="kn"):
    # returns translated text or raises
    if argostranslate is None:
        return None
    try:
        return argostranslate.translate.translate(text, from_code, to_code)
    except Exception:
        return None
