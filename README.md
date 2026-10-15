# Seasonal Anime Image Downloader

Your friendly neighborhood glorified image thief for seasonal anime 🎬

Download all anime cover images from any season to use with TierMaker or other tierlist creators!

## What This Does

Downloads anime cover images from AniList for a given season. Perfect for:

- Creating tierlists on TierMaker.com
- Building your own anime ranking tools
- Collecting seasonal anime artwork

## Features

- 🔍 Fetches seasonal anime from AniList API, sorted by popularity
- 🔄 Includes anime continuing from the previous season (with a configurable grace period)
- 📥 Downloads cover images in parallel with retry logic
- 📊 Saves metadata JSON for reference
- ⚡ Global rate limiting, and automatic waiting and retrying when AniList rate limits you
- 🛡️ Safe writes, so interrupted downloads never leave broken images behind
- ⏭️ Skips already downloaded images

## Installation

```bash
# Clone the repository
git clone https://github.com/Daiya404/Seasonal-Anime-Image-Downloader.git
cd Seasonal-Anime-Image-Downloader

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage (Auto-detect current season)

```bash
python -m src
```

### Specify Season and Year

```bash
python -m src -s Winter -y 2025
```

### Multiple Seasons and Years

```bash
# Several seasons and years (every combination, one folder each)
python -m src -s winter,spring -y 2025,2026

# Mix explicit years with a year list
python -m src -s winter:2024,spring -y 2025

# All four seasons of a year
python -m src -s any -y 2025

# A range of years
python -m src -s winter -y 2023-2025

# A whole year in one folder named after the year (includes shows with no season yet)
python -m src -s year:2027 -f tv -l 50

# Several whole years, one folder each
python -m src -s year -y 2025-2027

# One folder with everything from two seasons
python -m src -s winter,spring -y 2025 --merge

# The same, in a folder with a name of your choosing
python -m src -s winter,spring -y 2025 --merge "Winter and Spring 2025"
```

### Sorting

```bash
# The 30 best-rated TV shows of a season
python -m src -s fall -f tv -S score -l 30

# Newest start date first, alphabetical among shows that started on the same day
python -m src -s fall -S start:desc,title
```

### Example: Filtered Seasonal Run

```bash
python -m src \
  --season fall \
  --year 2025 \
  --out ./output \
  --format TV,ONA \
  --limit 50 \
  --title-language english,native \
  --no-json
```

## Arguments

| Argument           | Short | Description                                                                                                                                                                                                                                                       | Default        |
| ------------------ | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| `--season`         | `-s`  | Season(s), comma separated: Winter/Spring/Summer/Fall (`autumn` also works), `any` for all four, or `year` for the whole year including shows with no season yet. Add `:year` or `:start-end` to give one its own years, e.g. `winter:2025` or `winter:2023-2025` | Current season |
| `--year`           | `-y`  | Year(s) or ranges, comma separated, e.g. `2025, 2023-2026`. Applies to seasons without their own year                                                                                                                                                             | Current year   |
| `--out`            | `-o`  | Output directory                                                                                                                                                                                                                                                  | `seasonal`     |
| `--workers`        | `-w`  | Number of parallel download workers                                                                                                                                                                                                                               | 8              |
| `--delay`          | `-d`  | Minimum delay between image requests, shared by all workers (seconds)                                                                                                                                                                                             | 0.15           |
| `--grace-days`     | `-g`  | Days into a season a previous-season show must still air to count as continuing (seasons only)                                                                                                                                                                    | 21             |
| `--no-continuing`  |       | Exclude anime continuing from the previous season (seasons only)                                                                                                                                                                                                  | False          |
| `--no-json`        |       | Skip metadata JSON output                                                                                                                                                                                                                                         | False          |
| `--include-adult`  |       | Include adult/hentai content                                                                                                                                                                                                                                      | False          |
| `--format`         | `-f`  | Only download the specified formats, comma separated; mutually exclusive with `--exclude-format`                                                                                                                                                                  | All formats    |
| `--exclude-format` |       | Skip the specified formats, comma separated; mutually exclusive with `--format`                                                                                                                                                                                   | None           |
| `--limit`          | `-l`  | Keep only the N most popular titles per season, applied after format filters                                                                                                                                                                                      | All titles     |
| `--merge`          | `-m`  | Put everything into one folder (named `Merged`, or the name you give) instead of one per season. Duplicates are merged, and images from earlier runs that aren't part of this run are removed from that folder                                                    | False          |
| `--sort`           | `-S`  | Sort by `popularity`, `score`, `title`, `start`, `end`, `id`, or `mal_id`; add `:asc` or `:desc`. Controls ranks and `--limit`; popularity and id are added as tie-breakers, and missing values go last                                                           | popularity     |
| `--title-language` | `-t`  | File-name title priority: `romaji`, `english`, `native`; `romaji` is always the final fallback                                                                                                                                                                    | `romaji`       |
| `--force`          |       | Re-download images even if they already exist                                                                                                                                                                                                                     | False          |
| `--yes`            | `-Y`  | Skip the confirmation prompt for large runs (more than 5 seasons' worth, a whole year counts as 4)                                                                                                                                                                | False          |

### Merge Mode

With `--merge`, only files this tool created (named `rank - id - title.jpg`) are ever removed from the folder. Other files are left alone.

### Title Languages

Title languages are tried in the order provided. For example, `-t english,native` uses English
titles first, then native titles, then romaji. Existing files are renamed when the selected
language changes; images are not downloaded again.

### Large Runs

Runs covering more than 5 seasons' worth of anime ask for confirmation before downloading. A whole year counts as 4 seasons. Use `--yes` to skip the prompt, including when running without a terminal.

## Output Structure

```
seasonal/
├── Winter 2025/
│   ├── 001 - 12345 - Anime Title 1.jpg
│   ├── 002 - 67890 - Anime Title 2.jpg
│   ├── ...
│   └── metadata.json
└── seasonal_downloader.log
```

File names are `rank - AniList ID - title`, and `metadata.json` lists the anime in popularity order.

## Using with TierMaker

1. Run the downloader for your desired season
2. Go to [TierMaker.com](https://tiermaker.com)
3. Click "Create a Tier List"
4. Upload all the downloaded images
5. Create your rankings!

## Requirements

- Python 3.10+
- requests
- tqdm

## License

MIT License - See [LICENSE](LICENSE) file for details

## Disclaimer

This tool downloads publicly available cover images from AniList for personal use. Please respect AniList's terms of service and rate limits.

## Contributing

Pull requests welcome! Please feel free to submit issues or improvements.

---

_Made with ❤️ for the anime community_
