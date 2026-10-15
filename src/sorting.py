import difflib
import re
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from .utils import pick_title

# Sort keys, and whether the natural direction is descending (highest first)
SORT_KEYS = {
    "popularity": True,
    "score": True,
    "title": False,
    "start": False,
    "end": False,
    "id": False,
    "mal_id": False,
}

# Always added after the keys the user gives, so the order is fully deterministic
TIE_BREAKERS = ("popularity", "id")


@dataclass(frozen=True)
class SortKey:
    name: str
    descending: bool

    def __str__(self) -> str:
        return f"{self.name}:{'desc' if self.descending else 'asc'}"


def describe_sort(keys: Sequence[SortKey]) -> str:
    return ", ".join(str(key) for key in keys)


def parse_sort(values: list[str] | None) -> list[SortKey]:
    """
    Parse --sort values like ["score,", "title:desc"] into sort keys.

    Each key may end in :asc or :desc, otherwise its natural direction is used.
    Popularity and id are appended as tie-breakers unless already listed.
    """
    keys: list[SortKey] = []
    seen: set[str] = set()

    for value in values or []:
        for part in re.split(r"[,\s]+", value):
            if not part:
                continue
            name, sep, direction = part.lower().partition(":")

            if name not in SORT_KEYS:
                close = difflib.get_close_matches(name, SORT_KEYS, n=1)
                hint = f" Did you mean '{close[0]}'?" if close else ""
                raise ValueError(f"Unknown sort key '{name}'.{hint} Valid: {', '.join(SORT_KEYS)}")
            if sep and direction not in ("asc", "desc"):
                raise ValueError(f"Invalid direction '{direction}' for '{name}'. Use {name}:asc or {name}:desc")

            if name in seen:
                continue
            seen.add(name)
            keys.append(SortKey(name, SORT_KEYS[name] if not sep else direction == "desc"))

    if values and not keys:
        raise ValueError(f"--sort needs at least one key. Valid: {', '.join(SORT_KEYS)}")

    for name in TIE_BREAKERS:
        if name not in seen:
            seen.add(name)
            keys.append(SortKey(name, SORT_KEYS[name]))
    return keys


def _date_value(date: dict | None) -> tuple[int, int, int] | None:
    """Comparable AniList date; unknown month or day is treated as 1."""
    if not date or not date.get("year"):
        return None
    return (date["year"], date.get("month") or 1, date.get("day") or 1)


def sort_anime(
    anime_list: list[dict],
    keys: Sequence[SortKey],
    title_languages: Sequence[str] = ("romaji",),
) -> list[dict]:
    """Sort by several keys, placing missing values last for every key."""
    getters: dict[str, Callable[[dict], Any]] = {
        "popularity": lambda anime: anime.get("popularity"),
        "score": lambda anime: anime.get("averageScore"),
        "title": lambda anime: pick_title(anime, tuple(title_languages)).casefold(),
        "start": lambda anime: _date_value(anime.get("startDate")),
        "end": lambda anime: _date_value(anime.get("endDate")),
        "id": lambda anime: anime.get("id"),
        "mal_id": lambda anime: anime.get("idMal"),
    }

    result = list(anime_list)
    for key in reversed(keys):
        get = getters[key.name]
        present = [anime for anime in result if get(anime) is not None]
        missing = [anime for anime in result if get(anime) is None]
        present.sort(key=get, reverse=key.descending)
        result = present + missing
    return result
