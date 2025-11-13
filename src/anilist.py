# src/anilist.py

import requests
import logging

API_URL = "https://graphql.anilist.co"

# Season order
SEASON_ORDER = ["WINTER", "SPRING", "SUMMER", "FALL"]


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


def get_seasonal_anime(season: str, year: int, per_page: int = 100, include_adult: bool = False, include_continuing: bool = True):
    """
    Fetch seasonal anime from AniList API, including continuing anime from previous season
    
    Args:
        season: Season name (WINTER, SPRING, SUMMER, FALL)
        year: Year (e.g., 2025)
        per_page: Results per page (max 100)
        include_adult: Whether to include adult/hentai content (default: False)
        include_continuing: Whether to include anime continuing from previous season (default: True)
    
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
    logging.info(f"Fetching {season.upper()} {year} anime...")
    current_season_anime = _fetch_season(query, season, year, per_page, include_adult)
    
    results = current_season_anime.copy()
    current_ids = {anime['id'] for anime in current_season_anime}
    
    # Continuing anime from last season
    if include_continuing:
        prev_season, prev_year = get_previous_season(season, year)
        logging.info(f"Fetching continuing anime from {prev_season} {prev_year}...")
        
        prev_season_anime = _fetch_season(query, prev_season, prev_year, per_page, include_adult)
        
        # Filter for anime that are still airing/continuing
        continuing_anime = []
        for anime in prev_season_anime:
            # Skip if already in current season
            if anime['id'] in current_ids:
                continue
            
            # Check if anime is still airing or hasn't ended
            status = anime.get('status', '')
            end_date = anime.get('endDate', {})
            
            # Include if:
            # 1. Status is RELEASING (still airing)
            # 2. No end date set
            # 3. End date is in the future or current season
            if status == 'RELEASING' or not end_date or not end_date.get('year'):
                continuing_anime.append(anime)
                continue
            
            # Check if end date is after the start of current season
            end_year = end_date.get('year')
            end_month = end_date.get('month', 12)
            
            if end_year and end_year >= year:
                # Get approximate start month of current season
                season_start_month = {
                    'WINTER': 1, 'SPRING': 4, 'SUMMER': 7, 'FALL': 10
                }.get(season.upper(), 1)
                
                if end_year > year or (end_year == year and end_month >= season_start_month):
                    continuing_anime.append(anime)
        
        if continuing_anime:
            logging.info(f"Found {len(continuing_anime)} continuing anime from previous season")
            results.extend(continuing_anime)
        else:
            logging.info("No continuing anime found from previous season")
    
    return results


def _fetch_season(query: str, season: str, year: int, per_page: int, include_adult: bool):
    """
    Internal function to fetch anime for a specific season
    
    Args:
        query: GraphQL query string
        season: Season name (WINTER, SPRING, SUMMER, FALL)
        year: Year
        per_page: Results per page
        include_adult: Whether to include adult content
    
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
            "isAdult": include_adult
        }
        
        try:
            resp = requests.post(
                API_URL,
                json={"query": query, "variables": variables},
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            
            if "errors" in data:
                logging.error(f"GraphQL errors: {data['errors']}")
                break
            
            page_data = data.get("data", {}).get("Page", {})
            page_media = page_data.get("media", [])
            
            if not page_media:
                break
            
            # NO HENTAI
            if not include_adult:
                page_media = [anime for anime in page_media if not anime.get("isAdult", False)]
            
            results.extend(page_media)
            
            page_info = page_data.get("pageInfo", {})
            has_next = page_info.get("hasNextPage", False)
            
            if not has_next:
                break
            
            page += 1
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching page {page}: {e}")
            break
        except Exception as e:
            logging.error(f"Unexpected error on page {page}: {e}")
            break

    return results