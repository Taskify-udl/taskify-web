import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings

# Carpeta translations al lado de manage.py
TRANSLATIONS_DIR = Path(settings.BASE_DIR) / "translations"
DEFAULT_LANG = "es"


# @lru_cache(maxsize=None)
def load_lang(lang: str) -> dict:
    path = TRANSLATIONS_DIR / f"{lang}.json"
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def _resolve_dotted_key(data: dict, key: str):
    """
    Permite buscar "home.nav_my_services" dentro de dicts anidados.
    """
    parts = key.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    # si al final no es string, devolvemos None para que haga fallback
    return current if isinstance(current, str) else None


def t(key: str, lang: str | None = None) -> str:
    if lang is None:
        lang = DEFAULT_LANG

    data = load_lang(lang)
    value = _resolve_dotted_key(data, key)
    if value is not None:
        return value

    # Fallback al idioma por defecto
    if lang != DEFAULT_LANG:
        default_data = load_lang(DEFAULT_LANG)
        value = _resolve_dotted_key(default_data, key)
        if value is not None:
            return value

    return key