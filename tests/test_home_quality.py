"""Regression tests for the news home post-processing step."""
import unittest

from improve_home_quality import (
    improve, OLD_TITLE, OLD_DESCRIPTION, NEW_TITLE, NEW_DESCRIPTION,
)


class HomeQualityTests(unittest.TestCase):
    def setUp(self):
        self.sample = (
            '<html><head>' + OLD_TITLE + OLD_DESCRIPTION +
            '<style>body{color:black}</style></head>'
            '<body><main><section class="section">'
            '오늘의 브리핑</section>'
            '<div aria-label="실시간 뉴스 속보">'
            '<div class="label">실시간 뉴스</div>⚡ BREAKING'
            '</div></main></body></html>'
        )

    def test_restores_readable_cards_and_guide(self):
        result = improve(self.sample)
        self.assertIn('News feed fallback: update_news.py', result)
        self.assertIn('.news-live .grid>a{display:block', result)
        self.assertIn('id="reading-guide"', result)
        self.assertIn('href="/stock/guide/"', result)
        self.assertIn('외부 기사', result)
        self.assertIn(NEW_TITLE, result)
        self.assertIn(NEW_DESCRIPTION, result)
        self.assertNotIn(OLD_TITLE, result)
        self.assertNotIn('오늘의 브리핑', result)
        self.assertNotIn('⚡ BREAKING', result)

    def test_idempotent(self):
        once = improve(self.sample)
        self.assertEqual(once, improve(once))
        self.assertEqual(once.count('id="reading-guide"'), 1)
        self.assertEqual(once.count(NEW_TITLE), 1)
        self.assertEqual(once.count(NEW_DESCRIPTION), 1)

    def test_fails_before_writing_for_unknown_markup(self):
        with self.assertRaises(ValueError):
            improve('<html><body>unexpected</body></html>')
        with self.assertRaises(ValueError):
            improve(self.sample.replace(OLD_TITLE, '<title>Unknown site</title>'))


if __name__ == '__main__':
    unittest.main()
