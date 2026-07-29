#!/usr/bin/env python3
# ==============================================================================
# scrape-sitemap.py — Scrape all pages from a sitemap to clean markdown
# ==============================================================================
import argparse
import asyncio
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import requests
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "shared" / "datasets" / "scraped"

# Crawl4AI: strip nav, header, footer, form, hero section at HTML level
CRAWL_CONFIG = CrawlerRunConfig(
    excluded_tags=["nav", "header", "footer", "form", "script", "style", "svg"],
    excluded_selector="#service-form,.cta-modal,.gspb_row-id-gsbp-94659c1f-19f7,.site-header,.gspb_slidingPanel,#wp--skip-link--target,#wp-skip-link,#gspb_col-id-gsbp-e378eba,.cta-blog-bottom,.gspb-social-sharebox",
    page_timeout=30000,
)


def fetch_sitemap_urls(sitemap_url: str) -> list[str]:
    resp = requests.get(sitemap_url, timeout=30)
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "")
    if "xml" not in content_type and not resp.text.strip().startswith("<?xml"):
        raise ValueError(f"Sitemap URL returned non-XML content (Content-Type: {content_type})")
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        raise ValueError(f"Failed to parse sitemap XML: {e}") from e
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    urls = []
    for el in root.findall(".//sm:url/sm:loc", ns):
        urls.append(el.text.strip())
    for el in root.findall(".//sm:sitemap/sm:loc", ns):
        urls.append(el.text.strip())
    return urls


def url_to_filename(url: str, n: int) -> str:
    path = urlparse(url).path.strip("/") or "index"
    return f"{n:04d}_{re.sub(r'[^a-zA-Z0-9._-]', '_', path)[:80]}.md"


def filter_by_lang(urls: list[str], prefix: str | None) -> list[str]:
    if not prefix:
        return [u for u in urls if not re.search(r"https?://[^/]+/[a-z]{2}/", u)]
    return [u for u in urls if f"/{prefix}/" in u]


def exclude_urls(urls: list[str], patterns: list[str]) -> list[str]:
    if not patterns:
        return urls
    return [u for u in urls if not any(re.search(p, urlparse(u).path) for p in patterns)]


def detect_languages(urls: list[str]) -> dict[str, int]:
    stats: dict[str, int] = {"default": 0}
    for url in urls:
        m = re.match(r"https?://[^/]+/([a-z]{2})/", url)
        if m:
            stats[m.group(1)] = stats.get(m.group(1), 0) + 1
        else:
            stats["default"] += 1
    return stats


def clean_markdown(md: str) -> str:
    """Strip [Skip to content] link (nav/footer/forms handled by Crawl4AI)."""
    if not md:
        return md
    # Strip base64 placeholder images (lazy-load noise)
    md = re.sub(r"!\[[^\]]*\]\(data:image/[^)]+\)", "", md)
    # Collapse 3+ blank lines into 2
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


async def scrape_urls(urls: list[str], output_dir: Path, delay: float = 0.5):
    output_dir.mkdir(parents=True, exist_ok=True)
    total = len(urls)
    count = 0

    async with AsyncWebCrawler(verbose=False) as crawler:
        for i in range(0, total, 3):
            batch = urls[i : i + 3]
            tasks = [crawler.arun(url, config=CRAWL_CONFIG) for url in batch]
            results = await asyncio.gather(*tasks)

            for url, result in zip(batch, results):
                count += 1
                if not result.success:
                    print(f"  [{count}/{total}] ✗ {url}")
                    continue

                clean = clean_markdown(result.markdown)
                filename = url_to_filename(url, count)
                (output_dir / filename).write_text(
                    f"<!-- source: {url} -->\n\n{clean}", encoding="utf-8"
                )
                print(f"  [{count}/{total}] ✓ {url}")

            if i + 3 < total:
                await asyncio.sleep(delay)

    return count


async def main():
    parser = argparse.ArgumentParser(description="Scrape all pages from a sitemap")
    parser.add_argument("sitemap_url")
    parser.add_argument("kb_name")
    parser.add_argument("--lang-prefix", help="Language prefix (e.g., ka, ru)")
    parser.add_argument("--exclude", action="append", default=[], help="Exclude URL path regex (repeatable)")
    parser.add_argument("--list-langs", action="store_true")
    parser.add_argument("--delay", type=float, default=0.5)
    args = parser.parse_args()

    all_urls = fetch_sitemap_urls(args.sitemap_url)
    print(f"\nURLs: {len(all_urls)}")
    langs = detect_languages(all_urls)
    print(f"Languages: {langs}")

    if args.list_langs:
        for lang in langs:
            label = "default (omit --lang-prefix)" if lang == "default" else f"/{lang}/"
            print(f"  {langs[lang]:4d} pages — {label}")
        return

    urls = filter_by_lang(all_urls, args.lang_prefix)
    urls = exclude_urls(urls, args.exclude)
    label = args.lang_prefix or "default"
    if args.exclude:
        print(f"Excluding: {args.exclude}")
    print(f"Selected: {label} ({len(urls)} pages)")

    output_dir = OUTPUT_ROOT / args.kb_name
    print(f"Output: {output_dir}\n")

    saved = await scrape_urls(urls, output_dir, args.delay)
    print(f"\nDone: {saved} pages → {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
