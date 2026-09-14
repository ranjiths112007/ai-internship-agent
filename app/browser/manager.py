from __future__ import annotations

import logging
from typing import Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = Any  # type: ignore
    Page = Any  # type: ignore


class BrowserManager:
    def __init__(self, headless: bool | None = None):
        self.headless = headless if headless is not None else settings.playwright_headless
        self._playwright = None
        self.browser: Optional[Browser] = None

    def __enter__(self):
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright is not installed in the python environment.")
            return self
        try:
            self._playwright = sync_playwright().start()
            self.browser = self._playwright.chromium.launch(headless=self.headless)
        except Exception as e:
            logger.error(f"Failed to launch Playwright Chromium: {e}")
            self.browser = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass

    def create_page(self) -> Optional[Page]:
        if self.browser:
            context = self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            return context.new_page()
        return None
