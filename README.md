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
git clone https://github.com/Daiya404/Seasonal-Anime-Downloader.git
cd Seasonal-Anime-Downloader

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

### Full Options

```bash
python -m src \
  --season Fall \
  --year 2024 \
  --out ./output \
  --workers 10 \
  --delay 0.2 \
  --grace-days 14 \
  --no-json
```

## Arguments

| Argument           | Short | Description                                                                                      | Default        |
| ------------------ | ----- | ------------------------------------------------------------------------------------------------ | -------------- |
| `--season`         | `-s`  | Season name (Winter/Spring/Summer/Fall, `autumn` also works)                                     | Current season |
| `--year`           | `-y`  | Year (e.g., 2025)                                                                                | Current year   |
| `--out`            | `-o`  | Output directory                                                                                 | `seasonal`     |
| `--workers`        | `-w`  | Number of parallel download workers                                                              | 8              |
| `--delay`          | `-d`  | Minimum delay between image requests, shared by all workers (seconds)                            | 0.15           |
| `--grace-days`     | `-g`  | Days into a season a previous-season show must still air to count as continuing                  | 21             |
| `--no-continuing`  |       | Exclude anime continuing from the previous season                                                | False          |
| `--no-json`        |       | Skip metadata JSON output                                                                        | False          |
| `--include-adult`  |       | Include adult/hentai content                                                                     | False          |
| `--format`         | `-f`  | Only download the specified formats, comma separated; mutually exclusive with `--exclude-format` | All formats    |
| `--exclude-format` |       | Skip the specified formats, comma separated; mutually exclusive with `--format`                  | None           |
| `--limit`          | `-l`  | Keep only the N most popular titles, applied after format filters                               | All titles     |

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
