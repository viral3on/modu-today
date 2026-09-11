"""Shared URL discovery for crawl links and sitemap (standard library only)."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
BASE_URL = "https://modu.today"
EXCLUDE_DIRS = {".git", ".github", "node_modules", "__pycache__", ".vercel", "tests"}
# Standalone legacy pages have no hub connection or maintained editorial source.
# Keep them accessible; sitemap omission is not a noindex directive.
DEFERRED = {"yasun.html", "skhynix-split-analysis.html"}


class Metadata(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.title = ""
        self.description = ""
        self.canonical = ""
        self.noindex = False
        self.redirect = False
        self.links = []
        self.in_title = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "link" and "canonical" in attrs.get("rel", "").lower().split():
            self.canonical = attrs.get("href", "")
        if tag == "meta":
            name = attrs.get("name", "").lower()
            content = attrs.get("content", "")
            if name == "description":
                self.description = content
            if name in {"robots", "googlebot"} and "noindex" in content.lower():
                self.noindex = True
            if attrs.get("http-equiv", "").lower() == "refresh":
                self.redirect = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def html_to_url(path):
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        rel = ""
    elif rel.endswith("/index.html"):
        rel = rel[:-10]
    return BASE_URL + "/" + quote(rel, safe="/")


def exclusion(path, meta):
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return "non-public directory"
    if len(rel.parts) == 1 and rel.name.lower().startswith(("google", "naver")):
        return "verification file"
    if meta.noindex or meta.redirect:
        return "noindex or redirect"
    if meta.canonical and meta.canonical != html_to_url(path):
        return "canonical points elsewhere"
    if rel.as_posix() in DEFERRED:
        return "legacy standalone page: review before promoting"
    if len(rel.parts) == 3 and rel.parts[0] == "lotto" and rel.parts[1].isdigit():
        history = ROOT / "lotto/history/index.html"
        if history.exists() and f'/lotto/{rel.parts[1]}/' not in Metadata(history.read_text(encoding="utf-8")).links:
            return "draw outside maintained history hub"
    return ""


def pages():
    return [(p, Metadata(p.read_text(encoding="utf-8")))
            for p in sorted(ROOT.rglob("*.html"))
            if not any(part in EXCLUDE_DIRS for part in p.relative_to(ROOT).parts)]


def calculators():
    return [(p, m) for p, m in pages() if p.parent == ROOT / "calculator"
            and p.name != "index.html" and not exclusion(p, m)]


GROUPS = [
    "salary severance unemployment annual-leave parttime",
    "loan deposit compound exchange",
    "stock-return average-price dividend compound",
    "realtor registration-tax rent-tax area",
    "car-tax electricity customs percent bmi",
]


def related(path, catalog):
    peers = [item for item in catalog if item[0] != path]
    group = next((g.split() for g in GROUPS if path.stem in g.split()), [])
    return sorted(peers, key=lambda item: (item[0].stem not in group, item[0].name))[:4]
