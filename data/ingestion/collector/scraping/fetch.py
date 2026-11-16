"""Conservative public HTML fetcher with host allowlisting and polite request limits.

No authentication spoofing, anti-bot workarounds, private APIs or CAPTCHA bypasses.
Failures are reported, never silently replaced with fabricated product data.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOG = logging.getLogger(__name__)
USER_AGENT = "SmartCartCourseProject/0.2 (product identity research)"


class AccessError(RuntimeError):
    """Target page is unavailable, disallowed or not usable as product HTML."""


class HtmlFetcher:
    def __init__(self, *, delay_seconds: float = 2.0, timeout_seconds: int = 15,
                 respect_robots: bool = True, max_html_bytes: int = 3_000_000):
        if delay_seconds < 0 or timeout_seconds < 1 or max_html_bytes < 1024:
            raise ValueError("invalid fetch limits")
        self.delay = delay_seconds
        self.timeout = timeout_seconds
        self.respect_robots = respect_robots
        self.max_html_bytes = max_html_bytes
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
        retry = Retry(total=2, backoff_factor=1, status_forcelist=(500, 502, 503, 504),
                      allowed_methods=frozenset({"GET"}), respect_retry_after_header=True)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("https://", adapter)
        self.last_request = defaultdict(float)
        self.robot_rules: dict[str, RobotFileParser] = {}

    def _robots(self, url: str) -> bool:
        parts = urlparse(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin not in self.robot_rules:
            rules = RobotFileParser()
            rules.set_url(origin + "/robots.txt")
            try:
                response = self.session.get(origin + "/robots.txt", timeout=self.timeout)
                if response.status_code == 200:
                    rules.parse(response.text.splitlines())
                elif response.status_code in (401, 403, 429) or response.status_code >= 500:
                    raise AccessError(f"robots policy unavailable ({response.status_code}) for {origin}")
                else:
                    rules.parse([])
            except requests.RequestException as exc:
                raise AccessError(f"unable to check robots policy for {origin}: {exc}") from exc
            self.robot_rules[origin] = rules
        return self.robot_rules[origin].can_fetch(USER_AGENT, url)

    def get(self, url: str, *, allowed_hosts: set[str]) -> str:
        parts = urlparse(url)
        hostname = (parts.hostname or "").lower()
        if parts.scheme != "https" or hostname not in allowed_hosts or parts.username or parts.password:
            raise AccessError(f"URL host/scheme not allowed: {hostname}")
        if self.respect_robots and not self._robots(url):
            raise AccessError(f"robots.txt disallows fetching {hostname}{parts.path}")
        elapsed = time.monotonic() - self.last_request[hostname]
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request[hostname] = time.monotonic()
        try:
            with self.session.get(url, timeout=self.timeout, stream=True, allow_redirects=True) as response:
                final = urlparse(response.url)
                if final.scheme != "https" or (final.hostname or "").lower() not in allowed_hosts:
                    raise AccessError(f"cross-domain redirect blocked for {hostname}")
                if response.status_code in (401, 403, 429):
                    raise AccessError(f"access/rate limitation HTTP {response.status_code} at {hostname}")
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "").lower()
                if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                    raise AccessError(f"not an HTML document: {content_type or 'unknown type'}")
                body = bytearray()
                for chunk in response.iter_content(chunk_size=65536):
                    body.extend(chunk)
                    if len(body) > self.max_html_bytes:
                        raise AccessError(f"HTML exceeds {self.max_html_bytes} bytes")
                return bytes(body).decode(response.encoding or "utf-8", errors="replace")
        except requests.RequestException as exc:
            raise AccessError(f"fetch failed at {hostname}: {exc}") from exc
