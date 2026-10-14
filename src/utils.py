# src/utils.py

import re
from datetime import datetime

SEASON_START_MONTH = {"WINTER": 1, "SPRING": 4, "SUMMER": 7, "FALL": 10}
VALID_FORMATS = ("TV", "TV_SHORT", "MOVIE", "SPECIAL", "OVA", "ONA", "MUSIC")
VALID_TITLE_LANGUAGES = ("romaji", "english", "native")


def parse_choices(values: list[str], valid: tuple[str, ...], option: str) -> list[str]:
    """
    Parse CLI values like ["tv,", "ona"] or ["tv,ona"] into canonical values.

    Args:
        values: Raw tokens from argparse (each may contain commas)
        valid: Allowed values; matching is case-insensitive
        option: Option name, used in error messages

    Returns:
        Canonical values, deduplicated, in the order given

    Raises:
        ValueError: If a value is not in valid or nothing was given
    """
    canonical = {value.lower(): value for value in valid}
    items: list[str] = []
    for value in values:
        for part in value.split(","):
            key = part.strip().lower()
            if not key:
                continue
            if key not in canonical:
                raise ValueError(
                    f"Invalid value '{part.strip()}' for {option}. "
                    f"Valid: {', '.join(valid)}"
                )
            if canonical[key] not in items:
                items.append(canonical[key])
    if not items:
        raise ValueError(f"{option} needs at least one value. Valid: {', '.join(valid)}")
    return items


def pick_title(
    anime: dict,
    languages: tuple[str, ...] | list[str] = ("romaji",),
) -> str:
    """Pick the first non-empty title in the requested language order."""
    titles = anime.get("title") or {}
    for language in languages:
        value = (titles.get(language) or "").strip()
        if value:
            return value
    return str(anime.get("id"))


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """
    Sanitize a string to be used as a filename
    
    Args:
        name: Original string (anime title, etc.)
        max_length: Maximum filename length
    
    Returns:
        Sanitized filename string safe for all operating systems
    """
    # Remove or replace invalid characters for Windows/Linux/Mac
    # Invalid chars: < > : " / \ | ? *
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    
    # Strip leading/trailing whitespace and dots (Windows issue)
    name = name.strip().strip('.')
    
    # Truncate to max length
    if len(name) > max_length:
        name = name[:max_length].strip()
    
    # Fallback if empty after sanitization
    if not name:
        name = "untitled"
    
    return name


def get_current_season() -> str:
    """
    Determine the current anime season based on the current date,
    using the same season boundaries as AniList

    Returns:
        Season name: 'Winter', 'Spring', 'Summer', or 'Fall'
    """
    month = datetime.now().month

    if month <= 3:
        return "Winter"
    elif month <= 6:
        return "Spring"
    elif month <= 9:
        return "Summer"
    else:
        return "Fall"


def format_season_name(season: str, year: int) -> str:
    """
    Format season and year into a standardized string
    
    Args:
        season: Season name (case-insensitive)
        year: Year number
    
    Returns:
        Formatted string like "Winter 2025"
    """
    season = season.strip().capitalize()
    return f"{season} {year}"


def validate_season(season: str) -> bool:
    """
    Check if a season string is valid
    
    Args:
        season: Season name to validate
    
    Returns:
        True if valid, False otherwise
    """
    valid_seasons = {'winter', 'spring', 'summer', 'fall', 'autumn'}
    return season.lower().strip() in valid_seasons


def normalize_season(season: str) -> str:
    """
    Normalize season name (handles 'Autumn' -> 'Fall' conversion)
    
    Args:
        season: Season name
    
    Returns:
        Normalized season name for AniList API
    """
    season = season.strip().upper()
    if season == 'AUTUMN':
        return 'FALL'
    return season