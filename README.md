# Seasonal Tierlist Maker

Your friendly neighborhood glorified image thief for seasonal anime 🎬

## What This Does

Downloads anime cover images from AniList for a given season and generates an interactive HTML tierlist maker. Perfect for creating your personal anime rankings!

## Features

- 🔍 Fetches seasonal anime from AniList API
- 📥 Downloads cover images in parallel with retry logic
- 🎨 Generates drag-and-drop HTML tierlist interface
- 📊 Saves metadata JSON for reference
- ⚡ Rate-limited and concurrent downloads
- 🔄 Skips already downloaded images

## Installation

```bash
# Clone the repository
git clone https://github.com/Daiya404/Seasonal-Tierlist-Maker.git
cd Seasonal-Tierlist-Maker

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
  --no-html \
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
| `--no-html` | Skip HTML tierlist generation | False |
| `--no-json` | Skip metadata JSON output | False |

## Output Structure

```
seasonal/
├── Winter 2025/
│   ├── 001 - Anime Title 1.jpg
│   ├── 002 - Anime Title 2.jpg
│   ├── ...
│   ├── metadata.json
│   └── tierlist.html
└── seasonal_downloader.log
```

## Using the Tierlist

1. Open `tierlist.html` in your browser
2. Drag and drop anime covers into S, A, B, C, D, or F tiers
3. Take a screenshot when you're done!

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