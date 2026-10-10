# src/downloader.py

import os
import json
import time
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from tqdm import tqdm
from typing import List
from .utils import sanitize_filename


class Downloader:
    def __init__(self, out_dir: str, max_workers: int = 8, delay: float = 0.15, retries: int = 2, backoff: float = 1.0):
        self.out_dir = Path(out_dir)
        self.max_workers = max_workers
        self.delay = delay
        self.retries = retries
        self.backoff = backoff
        self.session = requests.Session()

    def _download_one(self, item, index, season_folder: Path):
        title = sanitize_filename(item.get("title", {}).get("romaji") or str(item.get("id")))
        url = item.get("coverImage", {}).get("large") or item.get("coverImage", {}).get("extraLarge")
        
        if not url:
            logging.warning(f"No cover image URL for {title}")
            return {"status": "failed", "file": None, "title": title}
        
        filename = f"{index:03d} - {title}.jpg"
        filepath = season_folder / filename

        if filepath.exists() and filepath.stat().st_size > 1024:
            logging.info(f"Skipping existing {filename}")
            return {"status": "skipped", "file": str(filepath), "title": title}

        attempt = 0
        while attempt <= self.retries:
            try:
                resp = self.session.get(url, timeout=30)
                resp.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                time.sleep(self.delay)
                return {"status": "ok", "file": str(filepath), "title": title}
            except Exception as e:
                attempt += 1
                logging.warning(f"Attempt {attempt} failed for {title}: {e}")
                if attempt <= self.retries:
                    time.sleep(self.backoff * attempt)
        
        return {"status": "failed", "file": str(filepath), "title": title}

    def download_all(self, anime_list: List[dict], season_name: str) -> List[dict]:
        season_folder = self.out_dir / season_name
        season_folder.mkdir(parents=True, exist_ok=True)

        with ThreadPoolExecutor(max_workers=self.max_workers) as exc:
            futures = [
                exc.submit(self._download_one, item, idx + 1, season_folder)
                for idx, item in enumerate(anime_list)
            ]

            for _ in tqdm(as_completed(futures), total=len(futures), desc="Downloading", unit="img"):
                pass

        results: List[dict] = []
        for fut, item in zip(futures, anime_list):
            try:
                results.append(fut.result())
            except Exception as e:
                logging.exception(f"A future failed outright: {e}")
                results.append({"status": "failed", "file": None, "title": str(item.get("id"))})

        meta_path = season_folder / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"season": season_name, "items": results}, f, ensure_ascii=False, indent=2)

        return results