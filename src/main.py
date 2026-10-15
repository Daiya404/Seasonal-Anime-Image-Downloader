# src/main.py

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
from .anilist import get_seasonal_anime, filter_by_format
from .downloader import Downloader
from .seasons import Job, parse_jobs
from .utils import (
    get_current_season,
    normalize_season,
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


@dataclass
class JobOutcome:
    """Result of one season: either an error, or download counts"""
    name: str
    error: str | None = None
    downloaded: int = 0
    skipped: int = 0
    failed: int = 0


def process_job(
    job: Job,
    args: argparse.Namespace,
    include_formats: list[str] | None,
    exclude_formats: list[str] | None,
    dl: Downloader,
) -> JobOutcome:
    """Fetch, filter and download one season"""
    logging.info("=" * 60)
    logging.info(f"Processing {job.name}")
    logging.info("=" * 60)

    anime_list = get_seasonal_anime(
        job.season,
        job.year,
        include_adult=args.include_adult,
        include_continuing=not args.no_continuing,
        grace_days=args.grace_days
    )
    logging.info(f"Successfully fetched {len(anime_list)} anime titles")

    if include_formats or exclude_formats:
        before = len(anime_list)
        anime_list = filter_by_format(anime_list, include_formats, exclude_formats)
        logging.info(f"Format filter kept {len(anime_list)} of {before} titles")

    if args.limit is not None and len(anime_list) > args.limit:
        anime_list = anime_list[:args.limit]
        logging.info(f"Limited to the top {args.limit} titles by popularity")

    if not anime_list:
        logging.warning(f"No anime found for {job.name}")
        return JobOutcome(job.name)

    results = dl.download_all(anime_list, job.name, write_json=not args.no_json)
    outcome = JobOutcome(
        job.name,
        downloaded=sum(1 for result in results if result.get("status") == "ok"),
        skipped=sum(1 for result in results if result.get("status") == "skipped"),
        failed=sum(1 for result in results if result.get("status") == "failed"),
    )
    logging.info(f"Download complete: {outcome.downloaded} downloaded, {outcome.skipped} skipped, {outcome.failed} failed")
    if not args.no_json:
        logging.info(f"Metadata saved to {dl.out_dir / job.name / 'metadata.json'}")
    return outcome


def main():
    parser = argparse.ArgumentParser(
        description="Seasonal anime cover downloader — glorified image thief",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-s",
        "--season",
        nargs="+",
        metavar="SEASON",
        help="Season(s), comma separated: winter, spring, summer, fall (autumn works) or any (all four). Add :YEAR (or :START-END) to give one its own years, e.g. winter:2025 or winter:2023-2025. Auto-detects the current season if not specified"
    )
    parser.add_argument(
        "-y",
        "--year",
        nargs="+",
        metavar="YEAR",
        help="Year(s) or ranges, comma separated, e.g. 2025, 2023-2026. Applies to seasons without their own year. Defaults to current year"
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
        help="Only keep the N most popular titles per season (applied after format filters)"
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
        "--force",
        action="store_true",
        help="Re-download images even if they already exist"
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
        title_languages = parse_choices(args.title_language, VALID_TITLE_LANGUAGES, "--title-language")
        jobs, warnings = parse_jobs(
            args.season,
            args.year,
            default_season=normalize_season(get_current_season()),
            default_year=datetime.now().year,
        )
    except ValueError as e:
        parser.error(str(e))
    if "romaji" not in title_languages:
        title_languages.append("romaji")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(out_dir / "seasonal_downloader.log")

    logging.info("=" * 60)
    logging.info("Seasonal Anime Image Downloader")
    logging.info("=" * 60)
    for warning in warnings:
        logging.warning(warning)
    logging.info(f"Seasons to process ({len(jobs)}): {', '.join(job.name for job in jobs)}")
    if not args.include_adult:
        logging.info("Filtering out adult content (use --include-adult to disable)")
    if not args.no_continuing:
        logging.info("Including anime continuing from previous season (use --no-continuing to disable)")

    logging.info(f"Using {args.workers} download workers")
    dl = Downloader(
        out_dir=out_dir,
        max_workers=args.workers,
        delay=args.delay,
        title_languages=title_languages,
        force=args.force
    )

    outcomes: list[JobOutcome] = []
    for job in jobs:
        try:
            outcomes.append(process_job(job, args, include_formats, exclude_formats, dl))
        except Exception as e:
            logging.error(f"{job.name} failed: {e}")
            outcomes.append(JobOutcome(job.name, error=str(e)))

    logging.info("=" * 60)
    logging.info("Summary")
    for outcome in outcomes:
        if outcome.error:
            logging.error(f"  {outcome.name}: FAILED ({outcome.error})")
        else:
            logging.info(f"  {outcome.name}: {outcome.downloaded} downloaded, {outcome.skipped} skipped, {outcome.failed} failed")
    logging.info(f"Images saved to: {out_dir}")
    logging.info("Upload them to TierMaker.com to create your tierlist!")
    logging.info("=" * 60)

    return 1 if any(outcome.error or outcome.failed for outcome in outcomes) else 0


if __name__ == '__main__':
    exit(main())