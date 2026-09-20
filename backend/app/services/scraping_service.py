"""
Scraping service – renders a URL and returns raw page material.

Three backends behind one `Scraper` interface:

* `PlaywrightScraper` – headless Chromium; executes JavaScript, captures the
                        rendered DOM, screenshot and page-level element data.
* `HttpxScraper`      – plain HTTP fetch (no JS) for lightweight environments.
* `MockScraper`       – deterministic synthetic storefront HTML seeded from the
                        URL so demo mode is realistic and repeatable.

Selection is driven by `SCRAPER_MODE` (mock | playwright | httpx).
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.config import get_settings
from app.data.mock_pages import build_mock_page

logger = logging.getLogger(__name__)


@dataclass
class ScrapeResult:
    url: str
    final_url: str
    status: int
    html: str
    title: str = ""
    screenshot_b64: Optional[str] = None
    dom_data: Dict[str, Any] = field(default_factory=dict)  # optional extra info from the browser
    scraper: str = "mock"
    duration_ms: int = 0


class ScrapeError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class Scraper:
    name = "base"

    async def fetch(self, url: str) -> ScrapeResult:
        raise NotImplementedError


class MockScraper(Scraper):
    name = "mock"

    async def fetch(self, url: str) -> ScrapeResult:
        seed = int(hashlib.md5(url.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        await asyncio.sleep(0.05)
        html, title = build_mock_page(url, rng)
        return ScrapeResult(url=url, final_url=url, status=200, html=html, title=title, scraper=self.name, duration_ms=rng.randint(350, 900))


class HttpxScraper(Scraper):
    name = "httpx"

    async def fetch(self, url: str) -> ScrapeResult:
        import time

        import httpx

        settings = get_settings()
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=settings.scraper_timeout_ms / 1000,
                                         headers={"User-Agent": "Mozilla/5.0 (compatible; DarkShieldBot/1.0)"}) as client:
                r = await client.get(url)
        except httpx.TimeoutException as exc:
            raise ScrapeError("ANALYSIS_TIMEOUT", "The website took too long to respond.") from exc
        except httpx.HTTPError as exc:
            raise ScrapeError("WEBSITE_UNAVAILABLE", f"Could not reach the website: {exc.__class__.__name__}") from exc
        if r.status_code >= 400:
            raise ScrapeError("WEBSITE_UNAVAILABLE", f"The website returned HTTP {r.status_code}.")
        if "text/html" not in r.headers.get("content-type", ""):
            raise ScrapeError("UNSUPPORTED_CONTENT", "The URL did not return an HTML page.")
        return ScrapeResult(url=url, final_url=str(r.url), status=r.status_code, html=r.text[:2_000_000], scraper=self.name,
                            duration_ms=int((time.perf_counter() - t0) * 1000))


# JS evaluated inside the page to collect UI signals that are hard to get from static HTML.
_PAGE_SCRIPT = """
() => {
  const visible = el => { const s = getComputedStyle(el); const r = el.getBoundingClientRect();
    return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0; };
  const text = el => (el.innerText || el.textContent || '').trim().replace(/\\s+/g,' ').slice(0,200);
  const buttons = [...document.querySelectorAll('button, [role=button], input[type=submit], a.btn, a.button')].filter(visible).map(text).filter(Boolean);
  const checkboxes = [...document.querySelectorAll('input[type=checkbox], input[type=radio]')].map(cb => {
    const lbl = cb.labels && cb.labels[0] ? text(cb.labels[0]) : (cb.closest('label') ? text(cb.closest('label')) : (cb.getAttribute('aria-label')||cb.name||''));
    return { type: cb.type, checked: cb.checked, label: lbl, required: cb.required, selector: cb.id ? '#'+cb.id : (cb.name ? `[name="${cb.name}"]` : null) };
  });
  const timers = [...document.querySelectorAll('[class*=countdown], [class*=timer], [id*=countdown], [id*=timer], time')].filter(visible).map(text).filter(Boolean);
  const popups = [...document.querySelectorAll('[role=dialog], .modal, [class*=popup], [class*=overlay]')].filter(visible).map(text).filter(Boolean);
  const smallText = [...document.querySelectorAll('small, .fine-print, [class*=disclaimer], sup')].filter(visible).map(text).filter(Boolean);
  const struck = [...document.querySelectorAll('s, del, strike, [class*=strike], [class*=was-price], [class*=old-price]')].filter(visible).map(text).filter(Boolean);
  const lowContrast = [...document.querySelectorAll('a, button')].filter(visible).filter(el => { const s = getComputedStyle(el); return parseFloat(s.opacity) < 0.6 || parseFloat(s.fontSize) < 11; }).map(text).filter(Boolean);
  return { buttons, checkboxes, timers, popups, smallText, struck, lowContrast, title: document.title, visibleText: document.body ? document.body.innerText.slice(0, 60000) : '' };
}
"""


class PlaywrightScraper(Scraper):  # pragma: no cover - requires browser binaries
    name = "playwright"

    async def fetch(self, url: str) -> ScrapeResult:
        import base64
        import time

        try:
            from playwright.async_api import Error as PWError, TimeoutError as PWTimeout, async_playwright
        except ImportError as exc:
            raise ScrapeError("SCRAPER_UNAVAILABLE", "Playwright is not installed. Run `playwright install chromium`.") from exc

        settings = get_settings()
        t0 = time.perf_counter()
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-dev-shm-usage", "--no-sandbox"])
            try:
                page = await browser.new_page(viewport={"width": 1366, "height": 900},
                                              user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36 DarkShield/1.0")
                # Block heavy media to speed things up
                await page.route("**/*.{png,jpg,jpeg,gif,webp,mp4,woff,woff2}", lambda route: route.abort())
                try:
                    resp = await page.goto(url, wait_until="domcontentloaded", timeout=settings.scraper_timeout_ms)
                    await page.wait_for_timeout(1200)  # let timers/popups render
                except PWTimeout as exc:
                    raise ScrapeError("ANALYSIS_TIMEOUT", "The website took too long to load.") from exc
                except PWError as exc:
                    raise ScrapeError("WEBSITE_UNAVAILABLE", "The website could not be loaded.") from exc
                status = resp.status if resp else 0
                if status >= 400:
                    raise ScrapeError("WEBSITE_UNAVAILABLE", f"The website returned HTTP {status}.")
                dom_data = await page.evaluate(_PAGE_SCRIPT)
                html = await page.content()
                shot = await page.screenshot(type="jpeg", quality=60, full_page=False)
                return ScrapeResult(url=url, final_url=page.url, status=status, html=html, title=dom_data.get("title", ""),
                                    screenshot_b64=base64.b64encode(shot).decode(), dom_data=dom_data, scraper=self.name,
                                    duration_ms=int((time.perf_counter() - t0) * 1000))
            finally:
                await browser.close()


def build_scraper(mode: Optional[str] = None) -> Scraper:
    mode = mode or get_settings().scraper_mode
    if mode == "playwright":
        return PlaywrightScraper()
    if mode == "httpx":
        return HttpxScraper()
    return MockScraper()
