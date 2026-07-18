#!/usr/bin/env python3

import html
import ipaddress
import json
import re
import socket
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import (
    parse_qs,
    quote_plus,
    unquote,
    urlparse,
)
from urllib.request import Request, urlopen

ROOT_DIR = Path(__file__).resolve().parents[4]

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 16) "
    "AppleWebKit/537.36 "
    "Chrome/131.0 Mobile Safari/537.36"
)

MAX_RESULTS = 10
MAX_DOWNLOAD_BYTES = 1_000_000
DEFAULT_TIMEOUT = 15


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self.current_href = ""
        self.current_text: list[str] = []
        self.capture = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag != "a":
            return

        attributes = {
            key: value or ""
            for key, value in attrs
        }

        href = attributes.get("href", "").strip()

        if href:
            self.current_href = href
            self.current_text = []
            self.capture = True

    def handle_data(self, data: str) -> None:
        if self.capture:
            cleaned = " ".join(data.split())

            if cleaned:
                self.current_text.append(cleaned)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self.capture:
            return

        title = " ".join(self.current_text).strip()

        if title and self.current_href:
            self.links.append({
                "title": title,
                "url": self.current_href,
            })

        self.current_href = ""
        self.current_text = []
        self.capture = False


def hostname_is_public(hostname: str) -> bool:
    try:
        addresses = socket.getaddrinfo(
            hostname,
            None,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror:
        return False

    if not addresses:
        return False

    for address in addresses:
        try:
            ip = ipaddress.ip_address(address[4][0])
        except ValueError:
            return False

        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False

    return True


def validate_public_url(value: str) -> str:
    parsed = urlparse(value)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are allowed")

    if not parsed.hostname:
        raise ValueError("URL hostname is missing")

    if not hostname_is_public(parsed.hostname):
        raise ValueError(
            "Private or local network destinations are blocked"
        )

    return value


def request_text(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> tuple[str, str]:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/json;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.8",
        },
    )

    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get(
            "Content-Type",
            "",
        )

        raw = response.read(MAX_DOWNLOAD_BYTES + 1)

    if len(raw) > MAX_DOWNLOAD_BYTES:
        raise ValueError("Downloaded page exceeded size limit")

    charset = "utf-8"
    match = re.search(
        r"charset=([a-zA-Z0-9_-]+)",
        content_type,
    )

    if match:
        charset = match.group(1)

    return (
        raw.decode(charset, errors="replace"),
        content_type,
    )


def clean_result_url(value: str) -> str:
    value = html.unescape(value.strip())

    if value.startswith("//"):
        value = "https:" + value

    parsed = urlparse(value)

    if "duckduckgo.com" in parsed.netloc:
        query = parse_qs(parsed.query)
        redirected = query.get("uddg", [""])[0]

        if redirected:
            value = unquote(redirected)

    if value.startswith("/url?"):
        query = parse_qs(urlparse(value).query)
        value = unquote(
            query.get("q", query.get("url", [""]))[0]
        )

    return value


def parse_generic_links(
    page: str,
    maximum_results: int,
) -> list[dict[str, str]]:
    parser = LinkParser()
    parser.feed(page)

    results = []
    seen = set()

    blocked_domains = {
        "duckduckgo.com",
        "html.duckduckgo.com",
        "lite.duckduckgo.com",
        "www.google.com",
        "google.com",
        "www.bing.com",
        "bing.com",
    }

    for item in parser.links:
        title = item["title"].strip()
        url = clean_result_url(item["url"])

        if len(title) < 4:
            continue

        if not url.startswith(("http://", "https://")):
            continue

        try:
            validate_public_url(url)
        except ValueError:
            continue

        domain = urlparse(url).netloc.lower()

        if domain in blocked_domains:
            continue

        if url in seen:
            continue

        seen.add(url)

        results.append({
            "title": title[:300],
            "url": url,
            "snippet": "",
            "domain": domain,
        })

        if len(results) >= maximum_results:
            break

    return results


def search_duckduckgo(
    query: str,
    maximum_results: int,
) -> list[dict[str, str]]:
    urls = [
        (
            "https://html.duckduckgo.com/html/?q="
            + quote_plus(query)
        ),
        (
            "https://lite.duckduckgo.com/lite/?q="
            + quote_plus(query)
        ),
    ]

    for url in urls:
        try:
            page, _ = request_text(url)
            results = parse_generic_links(
                page,
                maximum_results,
            )

            if results:
                return results
        except Exception:
            continue

    return []


def search_wikipedia(
    query: str,
    maximum_results: int,
) -> list[dict[str, str]]:
    url = (
        "https://en.wikipedia.org/w/api.php"
        "?action=query"
        "&list=search"
        "&format=json"
        "&utf8=1"
        "&srlimit="
        + str(maximum_results)
        + "&srsearch="
        + quote_plus(query)
    )

    try:
        text, _ = request_text(url)
        data = json.loads(text)
    except Exception:
        return []

    results = []

    for item in (
        data.get("query", {}).get("search", [])
    ):
        title = str(item.get("title", "")).strip()

        if not title:
            continue

        page_url = (
            "https://en.wikipedia.org/wiki/"
            + quote_plus(title.replace(" ", "_"))
        )

        snippet = re.sub(
            r"<[^>]+>",
            " ",
            str(item.get("snippet", "")),
        )
        snippet = " ".join(
            html.unescape(snippet).split()
        )

        results.append({
            "title": title,
            "url": page_url,
            "snippet": snippet,
            "domain": "en.wikipedia.org",
        })

    return results[:maximum_results]


def search_web(
    query: str,
    maximum_results: int,
) -> dict[str, Any]:
    query = query.strip()

    if not query:
        return {
            "success": False,
            "error": "Search query is required",
        }

    maximum_results = max(
        1,
        min(int(maximum_results), MAX_RESULTS),
    )

    provider_attempts = []

    duck_results = search_duckduckgo(
        query,
        maximum_results,
    )

    provider_attempts.append({
        "provider": "duckduckgo_html",
        "result_count": len(duck_results),
    })

    results = list(duck_results)

    if len(results) < maximum_results:
        wikipedia_results = search_wikipedia(
            query,
            maximum_results,
        )

        provider_attempts.append({
            "provider": "wikipedia_api",
            "result_count": len(wikipedia_results),
        })

        seen = {
            item["url"]
            for item in results
        }

        for item in wikipedia_results:
            if item["url"] in seen:
                continue

            results.append(item)
            seen.add(item["url"])

            if len(results) >= maximum_results:
                break

    return {
        "success": bool(results),
        "status": "web_search_complete",
        "query": query,
        "result_count": len(results),
        "results": results,
        "providers": provider_attempts,
        "error": (
            None
            if results
            else "All configured search providers returned no results"
        ),
    }


def strip_html(value: str) -> str:
    value = re.sub(
        r"(?is)<(script|style).*?>.*?</\1>",
        " ",
        value,
    )
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    value = html.unescape(value)
    return " ".join(value.split())


def fetch_public_page(url: str) -> dict[str, Any]:
    validated = validate_public_url(url)
    page, content_type = request_text(validated)
    text = strip_html(page)

    return {
        "success": True,
        "status": "public_page_fetched",
        "url": validated,
        "content_type": content_type,
        "text": text[:50_000],
        "characters": min(len(text), 50_000),
    }


def health_check() -> dict[str, Any]:
    return {
        "success": True,
        "status": "healthy",
        "network_required": True,
        "search_providers": [
            "duckduckgo_html",
            "duckduckgo_lite",
            "wikipedia_api",
        ],
        "private_network_access_blocked": True,
    }


def run(task: dict[str, Any]) -> dict[str, Any]:
    action = task.get("action")
    payload = task.get("payload", {})

    if not isinstance(payload, dict):
        payload = {}

    if action == "search_web":
        return search_web(
            query=str(payload.get("query", "")),
            maximum_results=int(
                payload.get("maximum_results", 5)
            ),
        )

    if action == "fetch_public_page":
        return fetch_public_page(
            str(payload.get("url", ""))
        )

    return {
        "success": False,
        "error": f"Unsupported web action: {action}",
    }
