import argparse
import logging
from pathlib import Path
from .anilist import get_seasonal_anime
from .downloader import Downloader, generate_tierlist_html
from .utils import get_current_season




def setup_logging(logfile: Path):
fmt = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=fmt, handlers=[
logging.FileHandler(logfile),
logging.StreamHandler()
])




def main():
parser = argparse.ArgumentParser(description="Seasonal anime cover downloader — glorified image thief")
parser.add_argument("--season", type=str, help="Season name, e.g. Winter, Spring, Summer, Fall")
parser.add_argument("--year", type=int, help="Year, e.g. 2026")
parser.add_argument("--out", type=str, default="seasonal", help="Output base directory")
parser.add_argument("--workers", type=int, default=8, help="Parallel download workers")
parser.add_argument("--delay", type=float, default=0.12, help="Per-worker delay between downloads (sec)")
parser.add_argument("--no-html", action="store_true", help="Do not generate tierlist HTML")
parser.add_argument("--no-json", action="store_true", help="Do not output metadata json")
args = parser.parse_args()


season = args.season or get_current_season()
year = args.year
if year is None:
from datetime import datetime
year = datetime.now().year


season_folder_name = f"{season} {year}"
out_dir = Path(args.out)
out_dir.mkdir(parents=True, exist_ok=True)


logfile = out_dir / "seasonal_downloader.log"
setup_logging(logfile)


logging.info(f"Fetching {season} {year} from AniList")
anime_list = get_seasonal_anime(season, year)
logging.info(f"Fetched {len(anime_list)} items")


dl = Downloader(out_dir=out_dir, max_workers=args.workers, delay=args.delay)
results = dl.download_all(anime_list, season_folder_name)


if not args.no_json:
logging.info("Metadata saved alongside images")


if not args.no_html:
html_path = generate_tierlist_html(out_dir / season_folder_name)
logging.info(f"Tierlist HTML generated: {html_path}")


logging.info("All done. Your glorified image theft stands ready.")




if __name__ == '__main__':
main()