#!/usr/bin/env python3
"""Check that all technology icon URLs in README.md return HTTP 200.

Reads the Technologies & Tools section, extracts every image src,
and validates each returns a successful HTTP status.
Exits with code 1 if any URL is broken.
"""

import re
import sys
import urllib.request
import urllib.error

README_PATH = "README.md"
SECTION_HEADER = "## 🚀 Technologies & Tools"
TIMEOUT = 15  # seconds per request


def extract_section(content: str, header: str) -> str:
    """Extract content from header until the next header or end of file."""
    lines = content.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith(header):
            start = i
            break
    if start is None:
        return ""

    # Collect lines until next top-level heading (##) or end
    section_lines = []
    for line in lines[start + 1 :]:
        if line.strip().startswith("## ") and not line.strip().startswith(header):
            break
        section_lines.append(line)
    return "\n".join(section_lines)


def extract_image_urls(html_section: str) -> list[tuple[str, str]]:
    """Extract (alt_text, url) pairs from <img> tags."""
    pattern = re.compile(r'<img[^>]*\s+src="([^"]+)"[^>]*\s+alt="([^"]*)"[^>]*>')
    return [(m.group(2), m.group(1)) for m in pattern.finditer(html_section)]


def check_url(alt: str, url: str) -> tuple[str, int | str, bool]:
    """Check a single URL. Returns (alt, status_or_error, is_ok)."""
    try:
        req = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": "Mozilla/5.0 (compatible; IconChecker/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            status = resp.status
            # Accept 200 and 304 (Not Modified — cached but valid)
            return (alt, status, status in (200, 304))
    except urllib.error.HTTPError as e:
        return (alt, f"HTTP {e.code}", False)
    except urllib.error.URLError as e:
        return (alt, str(e.reason), False)
    except Exception as e:
        return (alt, str(e), False)


def main() -> int:
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    section = extract_section(content, SECTION_HEADER)
    if not section:
        print(f"::error::Section '{SECTION_HEADER}' not found in {README_PATH}")
        return 1

    icons = extract_image_urls(section)
    if not icons:
        print(f"::error::No image tags found in section '{SECTION_HEADER}'")
        return 1

    print(f"Checking {len(icons)} icon URLs...\n")

    failed = 0
    results = []
    for alt, url in icons:
        alt_text, status, ok = check_url(alt, url)
        status_line = f"  [OK] {status}" if ok else f"  [FAIL] {status}"
        results.append((ok, alt_text, url, status_line))
        if not ok:
            failed += 1

        # Print in order
        print(f"  {alt_text}: {url}")
        print(status_line)
        print()

    summary = f"\n{'='*50}\n{len(icons)} icons checked, {failed} failed"
    if failed:
        print(f"{summary}\n::error::[FAIL] {failed} icon(s) returned errors")
    else:
        print(f"{summary}\n[OK] All icons OK")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
