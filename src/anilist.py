# src/anilist.py

import time
import requests
import logging
from datetime import date, timedelta
from .utils import SEASON_START_MONTH, format_season_name

API_URL = "https://graphql.anilist.co"

# Season order
SEASON_ORDER = ["WINTER", "SPRING", "SUMMER", "FALL"]


def _is_continuing(anime, season, year, grace_days):
    end = anime.get("endDate") or {}
    if not end.get("year"):
        return True  # no end date known, assume still running
    end_date = date(end["year"], end.get("month") or 12, end.get("day") or 28)
    season_start = date(year, SEASON_START_MONTH[season.upper()], 1)
    return end_date > season_start + timedelta(days=grace_days)

def get_previous_season(season: str, year: int):
    """
    Get the previous season and year
    
    Args:
        season: Current season (WINTER, SPRING, SUMMER, FALL)
        year: Current year
    
    Returns:
        Tuple of (previous_season, previous_year)
    """
    season_upper = season.upper()
    current_idx = SEASON_ORDER.index(season_upper)
    
    if current_idx == 0:  # Winter > previous Fall
        return SEASON_ORDER[-1], year - 1
    else:
        return SEASON_ORDER[current_idx - 1], year


def get_seasonal_anime(season: str, year: int, per_page: int = 50, include_adult: bool = False, include_continuing: bool = True, grace_days: int = 21):
    """
    Fetch seasonal anime from AniList API, including continuing anime from previous season

    Args:
        season: Season name (WINTER, SPRING, SUMMER, FALL)
        year: Year (e.g., 2025)
        per_page: Results per page (max 50)
        include_adult: Whether to include adult/hentai content (default: False)
        include_continuing: Whether to include anime continuing from previous season (default: True)
        grace_days: Days into the new season a previous-season anime must still be
            airing to count as continuing (default: 21)

    Returns:
        List of anime dictionaries with id, title, coverImage, siteUrl
    """
    query = """
    query ($season: MediaSeason, $year: Int, $page: Int, $perPage: Int, $isAdult: Boolean) {
        Page(page: $page, perPage: $perPage) {
            pageInfo {
                total
                perPage
                currentPage
                lastPage
                hasNextPage
            }
            media(season: $season, seasonYear: $year, type: ANIME, sort: POPULARITY_DESC, isAdult: $isAdult) {
                id
                popularity
                title { 
                    romaji
                    english
                    native 
                }
                coverImage { 
                    large
                    extraLarge 
                }
                siteUrl
                format
                episodes
                averageScore
                isAdult
                genres
                startDate {
                    year
                    month
                    day
                }
                endDate {
                    year
                    month
                    day
                }
                status
            }
        }
    }
    """

    # Current season
    logging.info(f"Fetching {format_season_name(season, year)} anime...")
    current_season_anime = _fetch_season(query, season, year, per_page, include_adult)
    
    results = current_season_anime.copy()
    current_ids = {anime['id'] for anime in current_season_anime}
    
    # Continuing anime from last season
    if include_continuing:
        prev_season, prev_year = get_previous_season(season, year)
        logging.info(f"Fetching continuing anime from {format_season_name(prev_season, prev_year)}...")
        
        prev_season_anime = _fetch_season(query, prev_season, prev_year, per_page, include_adult)
        
        # Filter for anime that are still airing/continuing
        continuing_anime = [
            a for a in prev_season_anime
            if a["id"] not in current_ids and _is_continuing(a, season, year, grace_days)
        ]
        
        if continuing_anime:
            logging.info(f"Found {len(continuing_anime)} continuing anime from previous season")
            results.extend(continuing_anime)
        else:
            logging.info("No continuing anime found from previous season")

    results.sort(key=lambda a: a.get("popularity") or 0, reverse=True)
    return results

def _post(query: str, variables: dict, retries: int = 3) -> dict:
    """POST to AniList, sleeping and retrying when rate limited (HTTP 429)"""
    for _ in range(retries):
        resp = requests.post(
            API_URL,
            json={"query": query, "variables": variables},
            timeout=30
        )
        if resp.status_code == 429:
            wait = int(resp.headers.get("Retry-After", 60))
            logging.warning(f"Rate limited by AniList, sleeping {wait}s")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    raise RuntimeError("AniList rate limit: retries exhausted")

def _fetch_season_filtered(query: str, season: str, year: int, per_page: int, is_adult: bool):
    """
    Internal function to fetch one page-through of a season, filtered strictly
    by AniList's isAdult flag

    Args:
        query: GraphQL query string
        season: Season name (WINTER, SPRING, SUMMER, FALL)
        year: Year
        per_page: Results per page
        is_adult: Strict filter passed to AniList. True returns ONLY adult
            media, False returns ONLY non-adult media (it is not an
            "include" switch)

    Returns:
        List of anime dictionaries
    """
    results = []
    page = 1

    while True:
        variables = {
            "season": season.upper(),
            "year": year,
            "page": page,
            "perPage": per_page,
            "isAdult": is_adult,
        }

        data = _post(query, variables)

        if "errors" in data:
            raise RuntimeError(f"AniList GraphQL errors on page {page}: {data['errors']}")

        page_data = (data.get("data") or {}).get("Page") or {}
        page_media = page_data.get("media", [])

        if not page_media:
            break

        results.extend(page_media)

        if not page_data.get("pageInfo", {}).get("hasNextPage", False):
            break

        page += 1

    return results

def _fetch_season(query: str, season: str, year: int, per_page: int, include_adult: bool):
    """
    Internal function to fetch anime for a specific season

    AniList's isAdult filter is binary, so including adult content takes two
    requests (non-adult, then adult). The results are merged, deduplicated by
    id, and sorted by popularity.

    Args:
        query: GraphQL query string
        season: Season name (WINTER, SPRING, SUMMER, FALL)
        year: Year
        per_page: Results per page
        include_adult: If True, also fetch adult media in addition to
            non-adult media; if False, fetch non-adult media only

    Returns:
        List of anime dictionaries, sorted by popularity (highest first)
    """
    flags = [False, True] if include_adult else [False]
    results, seen = [], set()
    for flag in flags:
        for anime in _fetch_season_filtered(query, season, year, per_page, flag):
            if anime["id"] not in seen:
                seen.add(anime["id"])
                results.append(anime)
    results.sort(key=lambda a: a.get("popularity") or 0, reverse=True)
    return results