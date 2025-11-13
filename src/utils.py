import re
from datetime import datetime


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
    Determine the current anime season based on the current date
    
    Returns:
        Season name: 'Winter', 'Spring', 'Summer', or 'Fall'
    """
    month = datetime.now().month
    
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:  # month in [9, 10, 11]
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