import argparse
import sys

from browser_scraper import BrowserScraperError, print_preview


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Render a JavaScript-heavy website with Playwright and print cleaned text."
    )
    parser.add_argument("url", nargs="?", default="https://openai.com")
    parser.add_argument("--limit", type=int, default=2_000)
    parser.add_argument("--links", type=int, default=10)
    args = parser.parse_args()

    try:
        print_preview(args.url, limit=args.limit, link_limit=args.links)
    except BrowserScraperError as exc:
        print(f"Scraping failed: {exc}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
