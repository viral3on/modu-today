"""Canonical, indexable URLs with Git dates, never checkout filesystem times."""
from datetime import datetime, timezone
import subprocess
import xml.etree.ElementTree as ET
from seo_catalog import ROOT, pages, exclusion, html_to_url


def git(*args):
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                            text=True, encoding="utf-8", check=True)
    return result.stdout.strip()


def lastmod(path):
    rel = path.relative_to(ROOT).as_posix()
    dependencies = [rel]
    if rel.startswith("calculator/"):
        dependencies += ["calculator/theme.js", "calculator/theme.css"]
    try:
        if git("rev-parse", "--is-shallow-repository") == "true":
            return None
        if git("status", "--porcelain", "--", *dependencies):
            return datetime.now(timezone.utc).date().isoformat()
        timestamp = git("log", "-1", "--format=%cI", "--", *dependencies)
        if timestamp:
            return datetime.fromisoformat(timestamp).astimezone(timezone.utc).date().isoformat()
    except (OSError, subprocess.CalledProcessError, ValueError):
        pass
    return None


def main():
    urlset = ET.Element("urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})
    for path, meta in sorted(pages(), key=lambda item: html_to_url(item[0])):
        if exclusion(path, meta):
            continue
        url = ET.SubElement(urlset, "url")
        ET.SubElement(url, "loc").text = html_to_url(path)
        modified = lastmod(path)
        if modified:
            ET.SubElement(url, "lastmod").text = modified
    ET.indent(urlset, space="  ")
    result = ET.tostring(urlset, encoding="utf-8", xml_declaration=True) + b"\n"
    target = ROOT / "sitemap.xml"
    if not target.exists() or target.read_bytes() != result:
        target.write_bytes(result)
    print(f"sitemap.xml: {len(urlset)} URLs")


if __name__ == "__main__":
    main()
