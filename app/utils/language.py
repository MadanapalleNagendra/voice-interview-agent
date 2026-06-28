"""
app/utils/language.py
Language detection and validation helpers.
"""

SUPPORTED = {"en", "hi", "de"}
LANG_NAMES = {"en": "English", "hi": "Hindi", "de": "German"}


def validate_language(lang: str) -> str:
    """Normalise and validate a language code. Falls back to 'en'."""
    lang = lang.lower().strip()
    if lang in SUPPORTED:
        return lang
    # Handle full names
    reverse = {v.lower(): k for k, v in LANG_NAMES.items()}
    return reverse.get(lang, "en")


def language_label(lang: str) -> str:
    return LANG_NAMES.get(lang, "English")
