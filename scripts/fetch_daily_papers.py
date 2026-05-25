#!/usr/bin/env python3
"""Fetch high-vote Hugging Face Daily Papers from hf-mirror.com."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import ssl
import subprocess
import sys
import textwrap
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "https://hf-mirror.com"
USER_AGENT = "Mozilla/5.0 (compatible; Codex Hugging Face Daily Papers skill)"


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


@dataclass
class Paper:
    paper_id: str
    title: str
    votes: int
    url: str
    abstract: str = ""


def yesterday_shanghai() -> str:
    try:
        from zoneinfo import ZoneInfo

        today = dt.datetime.now(ZoneInfo("Asia/Shanghai")).date()
    except Exception:
        today = dt.datetime.utcnow().date()
    return (today - dt.timedelta(days=1)).isoformat()


def fetch_text(url: str, timeout: int = 30) -> tuple[str, str]:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/markdown,*/*"})
    try:
        response_cm = urlopen(request, timeout=timeout, context=ssl_context())
        with response_cm as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            final_url = response.geturl()
    except URLError as exc:
        if "CERTIFICATE_VERIFY_FAILED" not in str(exc):
            raise
        with urlopen(request, timeout=timeout, context=ssl._create_unverified_context()) as response:
            raw = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
            final_url = response.geturl()
    return raw.decode(charset, errors="replace"), final_url


def fetch_page(url: str, timeout: int = 30) -> tuple[str, str]:
    text, final_url = fetch_text(url, timeout=timeout)
    if "<article" in text or "Markdown Content:" in text:
        return text, final_url

    try:
        completed = subprocess.run(
            ["curl", "-L", "--compressed", "-s", "-w", "\n%{url_effective}", url],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return text, final_url

    body, _, effective = completed.stdout.rpartition("\n")
    return body, effective or final_url


def strip_tags(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def extract_title(article: str, paper_id: str) -> str:
    patterns = [
        rf'<a[^>]+href="/papers/{re.escape(paper_id)}"[^>]*class="[^"]*text-balance[^"]*"[^>]*>(.*?)</a>',
        rf"<h3\b.*?</h3>",
    ]
    for pattern in patterns:
        match = re.search(pattern, article, flags=re.I | re.S)
        if match:
            title = strip_tags(match.group(1) if match.lastindex else match.group(0))
            if title and title.lower() != "view paper":
                return title
    return paper_id


def parse_papers(list_html: str, base_url: str, min_votes: int) -> list[Paper]:
    papers: list[Paper] = []
    seen: set[str] = set()
    articles = re.findall(r"<article\b.*?</article>", list_html, flags=re.I | re.S)
    for article in articles:
        id_match = re.search(r'href="/papers/([^"#?/]+)"', article)
        vote_match = re.search(r'class="leading-none">\s*([0-9]+)\s*<', article)
        if not id_match or not vote_match:
            continue
        paper_id = html.unescape(id_match.group(1))
        if paper_id in seen:
            continue
        seen.add(paper_id)
        votes = int(vote_match.group(1))
        if votes <= min_votes:
            continue
        title = extract_title(article, paper_id)
        papers.append(Paper(paper_id=paper_id, title=title, votes=votes, url=urljoin(base_url, f"/papers/{paper_id}")))
    papers.sort(key=lambda item: (-item.votes, item.title.lower()))
    return papers


def extract_title_from_markdown(markdown: str) -> str | None:
    if re.match(r"\s*<!doctype html", markdown, flags=re.I):
        return None
    match = re.search(r"^Title:\s*(.+)$", markdown, flags=re.M)
    if match:
        return match.group(1).strip()
    lines = [line.strip() for line in markdown.splitlines()]
    for line in lines:
        if line and not line.startswith(("URL Source:", "Markdown Content:")):
            if line not in {"Back to arXiv", "Why HTML?", "Report Issue", "Back to Abstract", "Download PDF"}:
                return line
    return None


def looks_like_section_heading(line: str) -> bool:
    compact = re.sub(r"\s+", "", line)
    return bool(
        re.match(r"^(\d+|[A-Z])\.?[A-Z][A-Za-z][A-Za-z0-9 -]{0,80}$", line)
        or re.match(r"^\d+[A-Z][A-Za-z0-9]+", compact)
        or compact in {"Introduction", "1Introduction", "References", "Conclusion"}
    )


def extract_abstract(markdown: str) -> str:
    if re.match(r"\s*<!doctype html", markdown, flags=re.I):
        return ""
    lines = [html.unescape(line.rstrip()) for line in markdown.splitlines()]
    starts = [
        idx
        for idx, line in enumerate(lines)
        if re.sub(r"^#+\s*", "", line.strip()).strip().lower() == "abstract"
    ]
    best = ""
    for start in starts:
        chunk: list[str] = []
        for line in lines[start + 1 :]:
            stripped = line.strip()
            if not stripped:
                if chunk:
                    chunk.append("")
                continue
            if chunk and stripped.startswith("#"):
                break
            if chunk and looks_like_section_heading(stripped):
                break
            if stripped in {"Back to arXiv", "Why HTML?", "Report Issue", "Back to Abstract", "Download PDF"}:
                continue
            chunk.append(stripped)
        text = re.sub(r"\s+", " ", " ".join(chunk)).strip()
        if len(text) > len(best):
            best = text
    return best


def enrich_with_details(papers: Iterable[Paper], base_url: str, sleep_seconds: float) -> None:
    for paper in papers:
        markdown_url = urljoin(base_url, f"/papers/{paper.paper_id}.md")
        try:
            markdown, _ = fetch_page(markdown_url)
        except (HTTPError, URLError, TimeoutError) as exc:
            paper.abstract = f"[Failed to fetch markdown detail: {exc}]"
            continue
        title = extract_title_from_markdown(markdown)
        if title:
            paper.title = title
        paper.abstract = extract_abstract(markdown) or "[No abstract found in markdown detail.]"
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)


def wrap(text: str, width: int = 96) -> str:
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False))


def render_markdown(papers: list[Paper], requested_date: str, source_url: str, final_url: str, min_votes: int) -> str:
    effective = ""
    match = re.search(r"/papers/date/(\d{4}-\d{2}-\d{2})", final_url)
    if match and match.group(1) != requested_date:
        effective = f"\n\n> Note: requested {requested_date}, but source redirected to {match.group(1)}."

    out = [
        f"# Hugging Face Daily Papers - {requested_date}",
        "",
        f"Source: {source_url}",
        f"Filter: votes > {min_votes}; sort: votes descending.",
    ]
    if effective.strip():
        out.extend(["", effective.strip()])
    out.append("")
    if not papers:
        out.append(f"No papers found with votes > {min_votes}.")
        return "\n".join(out).strip() + "\n"

    for index, paper in enumerate(papers, 1):
        out.extend(
            [
                f"## {index}. {paper.title}",
                "",
                f"- Votes: {paper.votes}",
                f"- URL: {paper.url}",
                "",
                wrap(paper.abstract),
                "",
            ]
        )
    return "\n".join(out).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=yesterday_shanghai(), help="Daily Papers date, YYYY-MM-DD. Defaults to yesterday in Asia/Shanghai.")
    parser.add_argument("--min-votes", type=int, default=5, help="Keep papers with votes greater than this number. Default: 5.")
    parser.add_argument("--limit", type=int, default=0, help="Optional maximum number of papers after sorting.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"Base URL. Default: {DEFAULT_BASE_URL}")
    parser.add_argument("--sleep", type=float, default=0.2, help="Delay between detail-page requests. Default: 0.2 seconds.")
    args = parser.parse_args()

    if not re.match(r"^\d{4}-\d{2}-\d{2}$", args.date):
        print("error: --date must be YYYY-MM-DD", file=sys.stderr)
        return 2

    base_url = args.base_url.rstrip("/")
    source_url = urljoin(base_url, f"/papers/date/{args.date}")
    try:
        list_html, final_url = fetch_page(source_url)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"error: failed to fetch {source_url}: {exc}", file=sys.stderr)
        return 1

    papers = parse_papers(list_html, base_url, args.min_votes)
    if args.limit and args.limit > 0:
        papers = papers[: args.limit]
    enrich_with_details(papers, base_url, args.sleep)
    print(render_markdown(papers, args.date, source_url, final_url, args.min_votes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
