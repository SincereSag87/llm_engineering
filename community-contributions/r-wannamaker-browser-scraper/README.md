# Browser-based scraper for JavaScript-rendered sites

This contribution completes the Week 1 extra web scraping exercise by adding a Playwright-based scraper. The original `week1/scraper.py` uses `requests` and BeautifulSoup, which only sees the initial HTML returned by the server. Modern sites such as `https://openai.com` often render important content with JavaScript after the first response, so a browser needs to load the page before parsing it.

## What changed

- Added `browser_scraper.py`, a small Playwright scraper that renders pages in Chromium before cleaning text with BeautifulSoup.
- Kept course-compatible functions:
  - `fetch_website_contents(url)`
  - `fetch_website_links(url)`
- Added explicit error handling for missing Playwright dependencies, missing browser binaries, navigation failures, timeouts, and pages with no readable text.
- Added `example.py` and `browser_scraper_demo.ipynb` showing the scraper on `https://openai.com`.

No API keys or `.env` values are needed.

## Setup

From this folder:

```bash
pip install -r requirements.txt
playwright install chromium
```

If you are using the repository virtual environment on Windows, run:

```powershell
uv pip install --python ..\..\.venv\Scripts\python.exe -r requirements.txt
..\..\.venv\Scripts\python.exe -m playwright install chromium
```

## Run the example

```bash
python example.py https://openai.com
```

The script prints a cleaned text preview and a short list of rendered links. You can also import the scraper in a notebook:

```python
from browser_scraper import fetch_website_contents, fetch_website_links

print(fetch_website_contents("https://openai.com"))
print(fetch_website_links("https://openai.com")[:10])
```

## Why browser-based scraping is needed

`requests.get()` downloads the raw server response. That is fast and works well for static pages, but it does not execute JavaScript. Playwright opens a real headless Chromium browser, waits for the page to render, and then gives BeautifulSoup the final DOM. This makes the Week 1 approach work on more modern websites while keeping the cleaning and summarization workflow familiar.
