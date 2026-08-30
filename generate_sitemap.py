from pathlib import Path
from urllib.parse import quote
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
BASE_URL = "https://modu.today"

EXCLUDE_ROOT_PREFIXES = ("google", "naver")
EXCLUDE_DIRS = {".git", ".github", "node_modules", "__pycache__", ".vercel"}

def should_include(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if path.suffix.lower() != ".html":
        return False
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return False
    if len(rel.parts) == 1:
        name = rel.name.lower()
        if name.startswith(EXCLUDE_ROOT_PREFIXES):
            return False
    return True

def html_to_url(path: Path) -> str:
    rel = path.relative_to(ROOT).as_posix()
    if rel == "index.html":
        return f"{BASE_URL}/"
    if rel.endswith("/index.html"):
        folder = rel[:-len("index.html")]
        encoded = "/".join(quote(part) for part in folder.split("/") if part)
        return f"{BASE_URL}/{encoded}/"
    encoded = "/".join(quote(part) for part in rel.split("/"))
    return f"{BASE_URL}/{encoded}"

def iso_date_from_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date().isoformat()

html_files = sorted(
    (p for p in ROOT.rglob("*.html") if should_include(p)),
    key=lambda p: html_to_url(p)
)

urlset = ET.Element("urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})

for path in html_files:
    url = ET.SubElement(urlset, "url")
    ET.SubElement(url, "loc").text = html_to_url(path)
    ET.SubElement(url, "lastmod").text = iso_date_from_mtime(path)

tree = ET.ElementTree(urlset)
ET.indent(tree, space="  ")
tree.write(ROOT / "sitemap.xml", encoding="utf-8", xml_declaration=True)

print(f"sitemap.xml generated: {len(html_files)} URLs")
for path in html_files:
    print(" -", html_to_url(path))
