"""Validate generated URLs, internal links and JavaScript-free discovery."""
from collections import deque
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
from seo_catalog import ROOT, BASE_URL, Metadata, pages, exclusion, html_to_url, calculators


def main():
    catalog = pages()
    by_url = {html_to_url(p): (p, m) for p, m in catalog}
    expected = {u for u, (p, m) in by_url.items() if not exclusion(p, m)}
    tree = ET.parse(ROOT / "sitemap.xml")
    urls = [e.text for e in tree.findall("{*}url/{*}loc")]
    assert len(urls) == len(set(urls)), "Duplicate sitemap URLs"
    assert set(urls) == expected, f"Sitemap mismatch: {set(urls) ^ expected}"
    graph = {}
    for url, (path, meta) in by_url.items():
        graph[url] = set()
        for href in meta.links:
            if href.startswith("/") and not href.startswith("//"):
                target = BASE_URL + urlsplit(href).path
                if target in by_url:
                    graph[url].add(target)
        # All generated links must point to an existing, eligible canonical page.
        text = path.read_text(encoding="utf-8")
        if "<!-- CRAWL_LINKS_START -->" in text:
            assert text.count("<!-- CRAWL_LINKS_START -->") == 1, path
            block = text.split("<!-- CRAWL_LINKS_START -->")[1].split("<!-- CRAWL_LINKS_END -->")[0]
            for href in Metadata(block).links:
                assert BASE_URL + href in expected, (path, href)
    distances = {BASE_URL + "/": 0}
    queue = deque(distances)
    while queue:
        source = queue.popleft()
        for target in graph[source]:
            if target not in distances:
                distances[target] = distances[source] + 1
                queue.append(target)
    for path, _ in calculators():
        assert distances.get(html_to_url(path), 999) <= 2, f"Calculator not within two static clicks: {path}"
        assert path.read_text(encoding="utf-8").count('data-static-related="1"') == 1, path
    for path, meta in catalog:
        if path.parent.parent == ROOT / "games" and not exclusion(path, meta):
            assert distances.get(html_to_url(path), 999) <= 2, path
    print(f"Validated {len(urls)} sitemap URLs; {len(calculators())} calculators within two static clicks")
    unreachable = sorted(expected - distances.keys())
    assert not unreachable, f"Sitemap pages not reachable from home: {unreachable}"


if __name__ == "__main__":
    main()
