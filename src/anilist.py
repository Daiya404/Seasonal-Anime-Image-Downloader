# src/nilist.py

import requests
import logging

API_URL = "https://graphql.anilist.co"


def get_seasonal_anime(season: str, year: int, per_page: int = 100, include_adult: bool = False):
    """
    Fetch seasonal anime from AniList API
    
    Args:
        season: Season name (WINTER, SPRING, SUMMER, FALL)
        year: Year (e.g., 2025)
        per_page: Results per page (max 100)
        include_adult: Whether to include adult/hentai content (default: False)
    
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
            }
        }
    }
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