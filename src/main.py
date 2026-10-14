# src/main.py

import argparse
import logging
from pathlib import Path
from datetime import datetime
from .anilist import get_seasonal_anime, filter_by_format
from .downloader import Downloader
from .utils import (
    get_current_season,
    validate_season,
    normalize_season,
    format_season_name,
    parse_choices,
    VALID_FORMATS,
    VALID_TITLE_LANGUAGES,
)


def setup_logging(logfile: Path):
    """Configure logging to both file and console"""
    fmt = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.FileHandler(logfile, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be 1 or greater")
    return number


def main():
    parser = argparse.ArgumentParser(
        description="Seasonal anime cover downloader — glorified image thief",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-s",
        "--season",
        type=str,
        help="Season name: Winter, Spring, Summer, or Fall (auto-detects if not specified)"
    )
    parser.add_argument(
        "-y",
        "--year",
        type=int,
        help="Year (e.g., 2025). Defaults to current year"
    )
    parser.add_argument(
        "-o",
        "--out",
        type=str,
        default="seasonal",
        help="Output base directory"
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=8,
        help="Number of parallel download workers"
    )
    parser.add_argument(
        "-d",
        "--delay",
        type=float,
        default=0.15,
        help="Minimum delay between image requests, shared by all workers (seconds)"
    )
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Do not output metadata JSON"
    )
    parser.add_argument(
        "--include-adult",
        action="store_true",
        help="Include adult/hentai content (default: False)"
    )
    parser.add_argument(
        "--no-continuing",
        action="store_true",
        help="Exclude anime continuing from previous season (default: includes continuing anime)"
    )
    format_group = parser.add_mutually_exclusive_group()
    format_group.add_argument(
        "-f",
        "--format",
        nargs="+",
        metavar="FORMAT",
        help="Only download these formats, comma separated (whitelist): TV, TV_SHORT, MOVIE, SPECIAL, OVA, ONA, MUSIC"
    )
    format_group.add_argument(
        "--exclude-format",
        nargs="+",
        metavar="FORMAT",
        help="Skip these formats, comma separated (blacklist). Can't be combined with --format"
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=positive_int,
        help="Only keep the N most popular titles (applied after format filters)"
    )
    parser.add_argument(
        "-t",
        "--title-language",
        nargs="+",
        metavar="LANG",
        default=["romaji"],
        help="Title language for file names: romaji, english, native. Comma separated in priority order; romaji is always the final fallback"
    )

    parser.add_argument(
        "-g",
        "--grace-days",
        type=int,
        default=21,
        help="Days into a season a previous-season show must still air to count as continuing"
    )

    args = parser.parse_args()

    try:
        include_formats = parse_choices(args.format, VALID_FORMATS, "--format") if args.format else None
        exclude_formats = parse_choices(args.exclude_format, VALID_FORMATS, "--exclude-format") if args.exclude_format else None
    except ValueError as e:
        parser.error(str(e))
    try:
        title_languages = parse_choices(args.title_language, VALID_TITLE_LANGUAGES, "--title-language")
    except ValueError as e:
        parser.error(str(e))
    if "romaji" not in title_languages:
        title_languages.append("romaji")

    if args.season:
        if not validate_season(args.season):
            parser.error(f"Invalid season '{args.season}'. Use winter, spring, summer, fall or autumn.")
        season = normalize_season(args.season)
    else:
        season = normalize_season(get_current_season())

    year = args.year or datetime.now().year

    season_folder_name = format_season_name(season, year)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    logfile = out_dir / "seasonal_downloader.log"
    setup_logging(logfile)

    logging.info("=" * 60)
    logging.info(f"Seasonal Anime Image Downloader - {season_folder_name}")
    logging.info("=" * 60)
    
    logging.info(f"Fetching {season_folder_name} from AniList API...")
    if not args.include_adult:
        logging.info("Filtering out adult content (use --include-adult to disable)")
    if not args.no_continuing:
        logging.info("Including anime continuing from previous season (use --no-continuing to disable)")
    
    try:
        anime_list = get_seasonal_anime(
            season, 
            year,
            include_adult=args.include_adult,
            include_continuing=not args.no_continuing,
            grace_days=args.grace_days
        )
        logging.info(f"Successfully fetched {len(anime_list)} anime titles")
    except Exception as e:
        logging.error(f"Failed to fetch anime list: {e}")
        return 1

    if include_formats or exclude_formats:
        before = len(anime_list)
        anime_list = filter_by_format(anime_list, include_formats, exclude_formats)
        logging.info(f"Format filter kept {len(anime_list)} of {before} titles")

    if args.limit is not None and len(anime_list) > args.limit:
        anime_list = anime_list[:args.limit]
        logging.info(f"Limited to the top {args.limit} titles by popularity")

    if not anime_list:
        logging.warning("No anime found for this season. Exiting.")
        return 0

    logging.info(f"Starting download with {args.workers} workers...")
    dl = Downloader(
        out_dir=out_dir,
        max_workers=args.workers,
        delay=args.delay,
        title_languages=title_languages
    )
    
    try:
        results = dl.download_all(anime_list, season_folder_name, write_json=not args.no_json)

        success = sum(1 for r in results if r.get("status") == "ok")
        skipped = sum(1 for r in results if r.get("status") == "skipped")
        failed = sum(1 for r in results if r.get("status") == "failed")

        logging.info(f"Download complete: {success} downloaded, {skipped} skipped, {failed} failed")

    except Exception as e:
        logging.error(f"Download failed: {e}")
        return 1

    if not args.no_json:
        logging.info(f"Metadata saved to {out_dir / season_folder_name / 'metadata.json'}")

    logging.info("=" * 60)
    logging.info(f"Images saved to: {out_dir / season_folder_name}")
    logging.info("Upload them to TierMaker.com to create your tierlist!")
    logging.info("=" * 60)
    
    return 0


if __name__ == '__main__':
    exit(main())