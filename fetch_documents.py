#!/usr/bin/env python3
"""
fetch_documents.py
Fetches source documents, strips HTML, and saves clean .txt files to documents/.

Run from inside your repo with the venv active:
    python fetch_documents.py

Requires: requests, beautifulsoup4
Install:  pip install requests beautifulsoup4
"""

import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup

DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), "documents")
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

# Mimic a real browser so sites don't block us
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def clean_soup(soup):
    """Remove boilerplate tags and return readable plain text."""
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)   # collapse blank lines
    text = re.sub(r"[ \t]{2,}", " ", text)   # collapse inline spaces
    return text.strip()


def save(filename, text):
    path = os.path.join(DOCUMENTS_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  ✓  {filename}  ({len(text):,} chars)")


def fetch_html(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    return clean_soup(soup)


def fetch_and_save(url, filename):
    try:
        text = fetch_html(url)
        save(filename, text)
    except Exception as e:
        print(f"  ✗  {filename}  — {e}")


# ── Reddit (JSON API — no account needed) ────────────────────────────────────

def fetch_reddit_search(query, filename, limit=25):
    """
    Search r/rutgers via Reddit's public JSON API and save matching posts.
    Each saved entry includes the post title, body, and top comments.
    """
    search_url = "https://www.reddit.com/r/rutgers/search.json"
    params = {"q": query, "restrict_sr": 1, "sort": "relevance", "limit": limit}
    headers = {**HEADERS, "Accept": "application/json"}

    try:
        resp = requests.get(search_url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        posts = resp.json()["data"]["children"]
    except Exception as e:
        print(f"  ✗  {filename}  — Reddit search failed: {e}")
        return

    lines = []
    for post in posts:
        d = post["data"]
        lines.append(f"=== POST: {d['title']} ===")
        if d.get("selftext") and d["selftext"] not in ("[removed]", "[deleted]"):
            lines.append(d["selftext"])
        lines.append(f"Link: https://reddit.com{d['permalink']}")

        # Fetch top-level comments for each post
        try:
            comments = fetch_reddit_comments(d["permalink"])
            if comments:
                lines.append("--- Comments ---")
                lines.extend(comments)
        except Exception:
            pass  # skip if comments fail

        lines.append("")  # blank line between posts
        time.sleep(0.5)  # be polite to Reddit

    save(filename, "\n".join(lines))


def fetch_reddit_comments(permalink, limit=10):
    """Return top-level comment bodies from a Reddit post."""
    url = f"https://www.reddit.com{permalink}.json?limit={limit}"
    resp = requests.get(url, headers={**HEADERS, "Accept": "application/json"}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    comments = []
    if len(data) > 1:
        for child in data[1]["data"]["children"]:
            body = child["data"].get("body", "")
            if body and body not in ("[removed]", "[deleted]"):
                comments.append(f"• {body}")
    return comments[:limit]


# ── Sources ───────────────────────────────────────────────────────────────────

# Plain HTML pages — requests + BeautifulSoup works fine
HTML_SOURCES = [
    (
        "http://www.vverma.net/succeeding-in-rutgers-cs.html",
        "vverma_succeeding_in_rutgers_cs.txt",
    ),
    (
        "https://www.cs.rutgers.edu/academics/undergraduate/course-synopses",
        "rutgers_course_synopses.txt",
    ),
    (
        "https://www.cs.rutgers.edu/academics/undergraduate/computer-science-course-structure",
        "rutgers_course_structure.txt",
    ),
    (
        "https://usacs.rutgers.edu/resources",
        "usacs_resources.txt",
    ),
]

# Reddit searches — pulls posts + comments via JSON API
REDDIT_SEARCHES = [
    ("computer science professors recommendations", "reddit_cs_professors.txt"),
    ("CS112 CS213 data structures tips advice",    "reddit_cs_core_courses.txt"),
    ("CS electives recommendations which to take", "reddit_cs_electives.txt"),
    ("CS336 databases CS314 principles",           "reddit_cs_upper_courses.txt"),
]

# Sites that block scrapers or need JavaScript — must be done manually
MANUAL_SOURCES = [
    (
        "https://www.ratemyprofessors.com/search/professors/826?q=*",
        "rmp_rutgers_cs.txt",
        "Go to the URL, open each professor, copy their reviews into this file.",
    ),
    (
        "https://medium.com/@rutgersusacs/rutgers-cs-electives-review-4b5ee979de2",
        "usacs_electives_review.txt",
        "Open in browser, copy the full article text.",
    ),
    (
        "https://medium.com/@rutgersusacs/guest-post-succeeding-in-rutgers-computer-science-by-v-48e6a5b75efb",
        "usacs_succeeding_cs.txt",
        "Open in browser, copy the full article text.",
    ),
]


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n── Fetching HTML pages ──────────────────────────────────")
    for url, filename in HTML_SOURCES:
        print(f"  Fetching {filename}...")
        fetch_and_save(url, filename)
        time.sleep(1)

    print("\n── Fetching Reddit posts + comments ─────────────────────")
    for query, filename in REDDIT_SEARCHES:
        print(f"  Searching: '{query}'...")
        fetch_reddit_search(query, filename)
        time.sleep(2)

    print("\n── Manual sources (JavaScript-rendered, can't auto-fetch) ──")
    for url, filename, instructions in MANUAL_SOURCES:
        print(f"  ⚠  documents/{filename}")
        print(f"     URL: {url}")
        print(f"     How: {instructions}")

    print("\n✓ Done — check the documents/ folder.")
    print("  Then manually create the ⚠ files above before running the pipeline.\n")
