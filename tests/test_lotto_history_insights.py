"""Regression tests for factual lottery history labels and navigation."""
import unittest

from lotto_history_insights import apply, render


class LottoHistoryInsightsTests(unittest.TestCase):
    def setUp(self):
        self.fixture = {'draws': [
            {'draw': 1241 - i, 'numbers': [1, 2, 3, 4, 5, 6]}
            for i in range(25)
        ]}

    def test_draw_lookup_is_based_on_real_rows(self):
        section = render(self.fixture)
        self.assertEqual(section.count('<option value="/lotto/'), 25)
        self.assertIn('value="/lotto/1241/"', section)
        self.assertIn('value="/lotto/1217/"', section)
        self.assertNotIn('value="/lotto/1216/"', section)
        self.assertIn('회차 선택', section)

    def test_duplicate_or_invalid_draws_are_not_offered(self):
        data = {'draws': self.fixture['draws'] + [
            {'draw': 1241, 'numbers': [1, 2, 3, 4, 5, 6]},
            {'draw': 1111, 'numbers': [1, 1, 2, 3, 4, 5]},
        ]}
        self.assertEqual(render(data).count('<option value="/lotto/'), 25)

    def test_store_coverage_and_counts_not_unique_shops(self):
        stores = {'1241': [{'region': '서울'}, {'region': '서울'}]}
        section = render(self.fixture, stores)
        self.assertIn('1개 회차', section)
        self.assertIn('2건', section)
        self.assertIn('고유 판매점 수', section)

    def test_region_unit_corrected_and_repeat_is_stable(self):
        original = ('<html><body><section class="region-box">'
                    '<h2>📍 최근 100회 1등 당첨지역 통계</h2>'
                    '<div class="meta">회차별 1등 당첨 판매점 소재지를 누적한 통계입니다. 당첨 확률을 의미하지 않습니다.</div>'
                    '<div class="region-stats"><div class="statbox"><b>전남광주</b><span>8곳</span></div></div>'
                    '<div class="meta">자동 10곳 · 수동 5곳</div></section>'
                    '<main class="list">목록</main></body></html>')
        once = apply(original, render(self.fixture))
        self.assertIn('전남·광주(원자료 통합)', once)
        self.assertIn('8건', once)
        self.assertIn('자동 10건 · 수동 5건', once)
        self.assertNotIn('8곳', once)
        self.assertEqual(once, apply(once, render(self.fixture)))


if __name__ == '__main__':
    unittest.main()
