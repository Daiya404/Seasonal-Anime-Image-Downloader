# Seasonal Anime Image Downloader

Your friendly neighborhood glorified image thief for seasonal anime 🎬

Download all anime cover images from any season to use with TierMaker or other tierlist creators!

## What This Does

Downloads anime cover images from AniList for a given season. Perfect for:
- Creating tierlists on TierMaker.com
- Building your own anime ranking tools
- Collecting seasonal anime artwork

## Features

- 🔍 Fetches seasonal anime from AniList API
- 📥 Downloads cover images in parallel with retry logic
- 📊 Saves metadata JSON for reference
- ⚡ Rate-limited and concurrent downloads
- 🔄 Skips already downloaded images

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
python -m src.main
```

### Specify Season and Year
```bash
python -m src.main --season Winter --year 2025
```

### Full Options
```bash
python -m src.main \
  --season Fall \
  --year 2024 \
  --out ./output \
  --workers 10 \
  --delay 0.1 \
  --no-json
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--season` | Season name (Winter/Spring/Summer/Fall) | Current season |
| `--year` | Year (e.g., 2025) | Current year |
| `--out` | Output directory | `seasonal` |
| `--workers` | Number of parallel download workers | 8 |
| `--delay` | Delay between downloads per worker (seconds) | 0.12 |
| `--no-json` | Skip metadata JSON output | False |

## Output Structure

```
seasonal/
├── Winter 2025/
│   ├── 001 - Anime Title 1.jpg
│   ├── 002 - Anime Title 2.jpg
│   ├── ...
│   └── metadata.json
└── seasonal_downloader.log
```

## Using with TierMaker

1. Run the downloader for your desired season
2. Go to [TierMaker.com](https://tiermaker.com)
3. Click "Create a Tier List"
4. Upload all the downloaded images
5. Create your rankings!

## Requirements

- Python 3.7+
- requests
- tqdm

## License

MIT License - See [LICENSE](LICENSE) file for details

## Disclaimer

This tool downloads publicly available cover images from AniList for personal use. Please respect AniList's terms of service and rate limits.

## Contributing

Pull requests welcome! Please feel free to submit issues or improvements.

---

*Made with ❤️ for the anime community*