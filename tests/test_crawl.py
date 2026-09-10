import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tempfile
import unittest
from unittest.mock import patch
import seo_catalog as catalog
import crawl_structure as crawl
import generate_sitemap as sitemap


class CrawlTests(unittest.TestCase):
    def test_new_calculator_and_repeat_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def put(rel, body):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(body, encoding="utf-8")
            put("calculator/index.html", '<html><title>계산기 0종</title><body><section class="calc-grid"></section><footer></footer></body></html>')
            for hub in ["games", "stock", "apt"]:
                put(f"{hub}/index.html", '<html><body><footer></footer></body></html>')
            put("calculator/new.html", '<html><title>새 계산기 &amp; 도구</title><meta name="description" content="새 기능"><body><footer></footer></body></html>')
            put("calculator/hidden.html", '<html><meta name="robots" content="noindex"><body></body></html>')
            with patch.object(catalog, "ROOT", root), patch.object(crawl, "ROOT", root), patch.object(sitemap, "ROOT", root), patch.object(sitemap, "lastmod", return_value=None):
                crawl.main()
                sitemap.main()
                first = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
                crawl.main()
                sitemap.main()
                self.assertEqual(first, {p: p.read_bytes() for p in first})
                hub = (root / "calculator/index.html").read_text(encoding="utf-8")
                self.assertIn('/calculator/new.html', hub)
                self.assertIn('계산기 1종', hub)
                self.assertNotIn('/calculator/hidden.html', hub)
                self.assertIn('data-static-related="1"', (root / "calculator/new.html").read_text(encoding="utf-8"))
                self.assertIn('/calculator/new.html', (root / "sitemap.xml").read_text(encoding="utf-8"))
                self.assertNotIn('/calculator/hidden.html', (root / "sitemap.xml").read_text(encoding="utf-8"))

    def test_exclusion_and_encoded_url(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(catalog, "ROOT", Path(directory)):
            root = Path(directory)
            for name, html in [("google123.html", ""), ("naver123.html", ""),
                               ("hidden.html", '<meta name="googlebot" content="noindex">'),
                               ("alias.html", '<link rel="canonical" href="https://modu.today/">'),
                               ("redirect.html", '<meta http-equiv="refresh" content="0;url=/">')]:
                self.assertTrue(catalog.exclusion(root / name, catalog.Metadata(html)))
            self.assertEqual(catalog.html_to_url(root / "한 글/index.html"), 'https://modu.today/%ED%95%9C%20%EA%B8%80/')

    def test_lastmod_uses_history_and_omits_unreliable_dates(self):
        path = sitemap.ROOT / "index.html"
        with patch.object(sitemap, "git", side_effect=["false", "", "2025-01-02T04:00:00+09:00"]):
            self.assertEqual(sitemap.lastmod(path), "2025-01-01")
        with patch.object(sitemap, "git", return_value="true"):
            self.assertIsNone(sitemap.lastmod(path))
        with patch.object(sitemap, "git", side_effect=OSError):
            self.assertIsNone(sitemap.lastmod(path))


if __name__ == "__main__":
    unittest.main()
