#!/usr/bin/env python3
# ==============================================================================
# crawl-site.py — Multi-page website crawler with language filtering
# Usage: shared/venv-crawl4ai/bin/python scripts/crawl-site.py <url> <kb-name> [--lang en] [--max-pages 500]
# ==============================================================================
import argparse
import asyncio
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from crawl4ai import AsyncWebCrawler

OUTPUT_ROOT = Path(__file__).resolve().parent.parent / "shared" / "datasets" / "scraped"


def url_to_filename(url: str, page_num: int) -> str:
    """Convert URL to a safe, numbered filename."""
    path = urlparse(url).path.strip("/")
    if not path:
        path = "index"
    clean = re.sub(r"[^a-zA-Z0-9._-]", "_", path)
    return f"{page_num:04d}_{clean[:80]}.md"


def detect_lang_from_url(url: str) -> str | None:
    """Detect language from URL path prefix like /en/, /it/, /de/."""
    path = urlparse(url).path
    match = re.match(r"^/([a-z]{2})(?:/|$)", path)
    return match.group(1) if match else None


def is_same_domain(url: str, base_domain: str) -> bool:
    """Check if URL belongs to the same domain."""
    parsed = urlparse(url)
    return parsed.netloc == base_domain or parsed.netloc.endswith("." + base_domain)


def is_page_url(url: str) -> bool:
    """Skip non-HTML resources (images, CSS, JS, PDFs, etc.)."""
    skip_exts = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
                 ".css", ".js", ".json", ".xml", ".ico", ".woff", ".woff2",
                 ".pdf", ".zip", ".mp4", ".avi", ".mov", ".mp3",
                 ".ttf", ".eot", ".map"}
    path = urlparse(url).path.lower()
    return not any(path.endswith(ext) for ext in skip_exts)


def extract_internal_links(html: str, base_url: str, base_domain: str) -> set[str]:
    """Extract all internal links from HTML."""
    links = set()
    for match in re.finditer(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE):
        href = match.group(1)
        # Skip anchors, javascript, mailto
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        full_url = urljoin(base_url, href)
        # Remove fragment
        full_url = full_url.split("#")[0]
        if is_same_domain(full_url, base_domain) and is_page_url(full_url):
            links.add(full_url)
    return links


async def crawl_site(
    start_url: str,
    kb_name: str,
    lang_filter: str | None = None,
    max_pages: int = 500,
    delay: float = 1.0,
):
    """Crawl an entire site, optionally filtering by language."""
    base_domain = urlparse(start_url).netloc
    output_dir = OUTPUT_ROOT / kb_name
    output_dir.mkdir(parents=True, exist_ok=True)

    visited: set[str] = set()
    to_visit: list[str] = [start_url]
    page_count = 0
    lang_stats: dict[str, int] = {}

    print(f"\n{'='*60}")
    print(f"Crawling: {start_url}")
    print(f"Domain:   {base_domain}")
    print(f"Output:   {output_dir}")
    if lang_filter:
        print(f"Language filter: {lang_filter}")
    print(f"Max pages: {max_pages}")
    print(f"{'='*60}\n")

    async with AsyncWebCrawler(verbose=False) as crawler:
        while to_visit and page_count < max_pages:
            # Take next batch (process a few concurrently for speed)
            batch = []
            while to_visit and len(batch) < 3:
                url = to_visit.pop(0)
                if url not in visited:
                    visited.add(url)
                    batch.append(url)

            if not batch:
                break

            # Crawl batch concurrently
            tasks = []
            for url in batch:
                tasks.append(crawler.arun(
                    url=url,
                    word_count_threshold=20,
                    remove_overlay_elements=True,
                    page_timeout=30000,
                ))
            results = await asyncio.gather(*tasks)

            for url, result in zip(batch, results):
                if not result.success:
                    print(f"  [{page_count+1}] FAILED: {url}")
                    continue

                # Detect language
                page_lang = detect_lang_from_url(url)
                if not page_lang and result.html:
                    # Fallback: check HTML lang attribute
                    m = re.search(r'<html[^>]+lang=["\']([a-z]{2})', result.html, re.IGNORECASE)
                    if m:
                        page_lang = m.group(1)

                # Filter by language if requested
                if lang_filter and page_lang != lang_filter:
                    continue

                # Discover new links
                if result.html and len(visited) < max_pages:
                    new_links = extract_internal_links(result.html, url, base_domain)
                    for link in new_links:
                        if link not in visited:
                            to_visit.append(link)

                # Save page
                page_count += 1
                filename = url_to_filename(url, page_count)
                filepath = output_dir / filename
                content = f"<!-- source: {url} -->\n<!-- lang: {page_lang or 'unknown'} -->\n\n{result.markdown}"
                filepath.write_text(content, encoding="utf-8")

                lang_stats[page_lang or "unknown"] = lang_stats.get(page_lang or "unknown", 0) + 1
                print(f"  [{page_count}] {url}  lang={page_lang or '?'}")

            # Be polite — delay between batches
            if to_visit and page_count < max_pages:
                await asyncio.sleep(delay)

    # Summary
    print(f"\n{'='*60}")
    print(f"Crawl complete: {page_count} pages saved")
    print(f"Languages found: {lang_stats}")
    print(f"Output: {output_dir}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Multi-page website crawler")
    parser.add_argument("url", help="Starting URL")
    parser.add_argument("kb_name", help="Knowledge base name (output folder)")
    parser.add_argument("--lang", help="Filter by language code (e.g., en, it, de, fr)")
    parser.add_argument("--max-pages", type=int, default=500, help="Maximum pages to crawl")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between batches (seconds)")
    args = parser.parse_args()

    asyncio.run(crawl_site(
        start_url=args.url,
        kb_name=args.kb_name,
        lang_filter=args.lang,
        max_pages=args.max_pages,
        delay=args.delay,
    ))


if __name__ == "__main__":
    main()
