# src/main.py

import argparse
import logging
from pathlib import Path
from datetime import datetime
from .anilist import get_seasonal_anime
from .downloader import Downloader
from .utils import get_current_season


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


def main():
    parser = argparse.ArgumentParser(
        description="Seasonal anime cover downloader — glorified image thief",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--season",
        type=str,
        help="Season name: Winter, Spring, Summer, or Fall (auto-detects if not specified)"
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Year (e.g., 2025). Defaults to current year"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="seasonal",
        help="Output base directory"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of parallel download workers"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.12,
        help="Per-worker delay between downloads (seconds)"
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
    
    args = parser.parse_args()

    season = args.season or get_current_season()
    year = args.year or datetime.now().year

    season_folder_name = f"{season} {year}"
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    logfile = out_dir / "seasonal_downloader.log"
    setup_logging(logfile)

    logging.info("=" * 60)
    logging.info(f"Seasonal Anime Image Downloader - {season} {year}")
    logging.info("=" * 60)
    
    logging.info(f"Fetching {season} {year} from AniList API...")
    if not args.include_adult:
        logging.info("Filtering out adult content (use --include-adult to disable)")
    if not args.no_continuing:
        logging.info("Including anime continuing from previous season (use --no-continuing to disable)")
    
    try:
        anime_list = get_seasonal_anime(
            season, 
            year, 
            include_adult=args.include_adult,
            include_continuing=not args.no_continuing
        )
        logging.info(f"Successfully fetched {len(anime_list)} anime titles")
    except Exception as e:
        logging.error(f"Failed to fetch anime list: {e}")
        return 1

    if not anime_list:
        logging.warning("No anime found for this season. Exiting.")
        return 0

    logging.info(f"Starting download with {args.workers} workers...")
    dl = Downloader(
        out_dir=out_dir,
        max_workers=args.workers,
        delay=args.delay
    )
    
    try:
        results = dl.download_all(anime_list, season_folder_name)
        
        success = sum(1 for r in results if r.get("status") == "ok")
        skipped = sum(1 for r in results if r.get("status") == "skipped")
        failed = sum(1 for r in results if r.get("status") == "failed")
        
        logging.info(f"Download complete: {success} downloaded, {skipped} skipped, {failed} failed")
        
    except Exception as e:
        logging.error(f"Download failed: {e}")
        return 1

    if not args.no_json:
        logging.info("Metadata saved alongside images")

    logging.info("=" * 60)
    logging.info(f"Images saved to: {out_dir / season_folder_name}")
    logging.info("Upload them to TierMaker.com to create your tierlist!")
    logging.info("=" * 60)
    
    return 0


if __name__ == '__main__':
    exit(main())