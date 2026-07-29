#!/usr/bin/env python3
# ==============================================================================
# scrape-website.py — Crawl a website to LLM-ready markdown via Crawl4AI
# Usage: shared/venv-crawl4ai/bin/python scripts/scrape-website.py <url> <kb-name>
# ==============================================================================
import asyncio
import re
import sys
from pathlib import Path

from crawl4ai import AsyncWebCrawler

OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "shared" / "datasets" / "scraped"


def url_to_filename(url: str) -> str:
    """Convert a URL into a safe filename."""
    clean = re.sub(r"^https?://", "", url)
    clean = re.sub(r"[^a-zA-Z0-9._-]", "_", clean)
    return clean.rstrip("_")[:100] + ".md"


async def scrape_single(url: str, output_dir: Path):
    """Scrape one URL and save as .md."""
    print(f"  Fetching: {url}")
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(
            url=url,
            word_count_threshold=10,       # skip near-empty pages
            remove_overlay_elements=True,   # kill cookie banners, popups
            page_timeout=30000,             # 30s timeout per page
        )
    if not result.success:
        print(f"  FAILED: {url}")
        return

    filename = url_to_filename(url)
    filepath = output_dir / filename
    # Prepend original URL as a comment for traceability
    content = f"<!-- source: {url} -->\n\n{result.markdown}"
    filepath.write_text(content, encoding="utf-8")
    print(f"  Saved: {filepath.name} ({len(result.markdown)} chars)")


async def main():
    if len(sys.argv) < 3:
        print("Usage: scrape-website.py <url> <kb-name>")
        print("Example: scrape-website.py https://docs.python.org/3/ python-docs")
        sys.exit(1)

    url = sys.argv[1]
    kb_name = sys.argv[2]

    output_dir = OUTPUT_ROOT / kb_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nScraping: {url}")
    print(f"Output:   {output_dir}\n")

    await scrape_single(url, output_dir)

    print(f"\nDone. {kb_name}/ → upload to Open WebUI Knowledge.")


if __name__ == "__main__":
    asyncio.run(main())
