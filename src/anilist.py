import requests


API_URL = "https://graphql.anilist.co"


# Keep a relatively small page size and allow iteration if >100 results needed
def get_seasonal_anime(season: str, year: int, per_page: int = 100):
query = """
query ($season: MediaSeason, $year: Int, $page: Int, $perPage: Int) {
Page(page: $page, perPage: $perPage) {
pageInfo { total, perPage, currentPage }
media(season: $season, seasonYear: $year, type: ANIME, sort: POPULARITY_DESC) {
id
title { romaji, native }
coverImage { large, extraLarge }
siteUrl
}
}
}
"""


results = []
page = 1
while True:
variables = {"season": season.upper(), "year": year, "page": page, "perPage": per_page}
resp = requests.post(API_URL, json={"query": query, "variables": variables}, timeout=30)
resp.raise_for_status()
data = resp.json()
page_media = data["data"]["Page"]["media"]
if not page_media:
break
results.extend(page_media)
page_info = data["data"]["Page"]["pageInfo"]
if page_info["currentPage"] * page_info["perPage"] >= page_info.get("total", len(results)):
break
page += 1


return results