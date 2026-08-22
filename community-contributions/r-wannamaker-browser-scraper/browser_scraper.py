from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

try:
    from playwright.sync_api import (
        Error as PlaywrightError,
        TimeoutError as PlaywrightTimeoutError,
        sync_playwright,
    )
except ImportError:  # pragma: no cover - exercised when dependency is missing
    sync_playwright = None
    PlaywrightError = Exception
    PlaywrightTimeoutError = TimeoutError


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/117.0.0.0 Safari/537.36"
)


class BrowserScraperError(Exception):
    """Raised when a browser-rendered page cannot be scraped."""


class BrowserDependencyError(BrowserScraperError):
    """Raised when Playwright or its browser binaries are not available."""


@dataclass
class RenderedWebsite:
    url: str
    title: str
    text: str
    links: list[str]

    def get_contents(self, limit: int = 2_000) -> str:
        """Return title and text in the same shape as the course scraper."""
        return (self.title + "\n\n" + self.text)[:limit]


def _require_playwright():
    if sync_playwright is None:
        raise BrowserDependencyError(
            "Playwright is not installed. Run: pip install playwright"
        )


def _clean_text_and_links(html: str, base_url: str) -> tuple[str, list[str]]:
    soup = BeautifulSoup(html, "html.parser")

    if soup.body:
        for irrelevant in soup.body(
            ["script", "style", "noscript", "svg", "img", "input", "button"]
        ):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = soup.get_text(separator="\n", strip=True)

    links = []
    for link in soup.find_all("a"):
        href = link.get("href")
        if href and not href.startswith(("mailto:", "tel:", "javascript:")):
            links.append(urljoin(base_url, href))

    return text, sorted(set(links))


def _render_html(
    url: str,
    *,
    timeout: int = 20_000,
    wait_until: str = "domcontentloaded",
    extra_wait_ms: int = 1_000,
    headless: bool = True,
) -> tuple[str, str]:
    _require_playwright()

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=headless)
            try:
                page = browser.new_page(
                    user_agent=DEFAULT_USER_AGENT,
                    viewport={"width": 1366, "height": 900},
                )
                response = page.goto(url, wait_until=wait_until, timeout=timeout)

                if response is None:
                    raise BrowserScraperError(f"No response received for {url}")
                if response.status >= 400:
                    raise BrowserScraperError(
                        f"Navigation failed for {url}: HTTP {response.status}"
                    )

                try:
                    page.wait_for_load_state("networkidle", timeout=5_000)
                except PlaywrightTimeoutError:
                    pass

                if extra_wait_ms:
                    page.wait_for_timeout(extra_wait_ms)

                title = page.title() or "No title found"
                return title, page.content()
            finally:
                browser.close()
    except PlaywrightTimeoutError as exc:
        raise BrowserScraperError(
            f"Timed out while loading {url} after {timeout} ms"
        ) from exc
    except PlaywrightError as exc:
        message = str(exc)
        if "Executable doesn't exist" in message or "playwright install" in message:
            raise BrowserDependencyError(
                "Playwright is installed, but browser binaries are missing. "
                "Run: playwright install chromium"
            ) from exc
        raise BrowserScraperError(f"Could not load {url}: {message}") from exc
    except OSError as exc:
        raise BrowserScraperError(
            f"Could not start Playwright's browser process: {exc}"
        ) from exc


def scrape_rendered_website(
    url: str,
    *,
    timeout: int = 20_000,
    headless: bool = True,
    extra_wait_ms: int = 1_000,
) -> RenderedWebsite:
    """
    Render a JavaScript-heavy page in Chromium and return cleaned text and links.

    This mirrors the Week 1 BeautifulSoup scraper's output style, but it first
    lets a real browser run the site's JavaScript.
    """
    title, html = _render_html(
        url,
        timeout=timeout,
        headless=headless,
        extra_wait_ms=extra_wait_ms,
    )
    text, links = _clean_text_and_links(html, url)

    if not text.strip():
        raise BrowserScraperError(f"No readable text found at {url}")

    return RenderedWebsite(url=url, title=title, text=text, links=links)


def fetch_website_contents(url: str, limit: int = 2_000) -> str:
    """Course-compatible replacement for week1.scraper.fetch_website_contents."""
    return scrape_rendered_website(url).get_contents(limit=limit)


def fetch_website_links(url: str) -> list[str]:
    """Course-compatible replacement for week1.scraper.fetch_website_links."""
    return scrape_rendered_website(url).links


def print_preview(url: str, *, limit: int = 2_000, link_limit: int = 10) -> None:
    """Small helper used by the example script and notebook."""
    website = scrape_rendered_website(url)
    print(website.get_contents(limit=limit))
    print("\nLinks:")
    for link in website.links[:link_limit]:
        print(f"- {link}")


def scrape_many(urls: Iterable[str]) -> dict[str, str]:
    """Scrape several pages and keep errors attached to their URLs."""
    results = {}
    for url in urls:
        try:
            results[url] = fetch_website_contents(url)
        except BrowserScraperError as exc:
            results[url] = f"Error: {exc}"
    return results
