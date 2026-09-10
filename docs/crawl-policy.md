# 자동 크롤링 구조

## 분류와 운영 기준

Search Console의 개별 URL 상태를 조회한 분류가 아니라 저장소의 콘텐츠와 링크를 기준으로 한 편집상 분류다. 수동 요청 후 색인이 빨랐다는 사실만으로 품질 문제 부재나 향후 자동 색인을 보장할 수 없다.

1. 검색 유입 가치가 높은 도구: 계산기 21개와 게임 3개. 홈 → 기존 허브 → 세부 페이지까지 정적 링크 두 번으로 도달한다. 계산기는 주제별 관련 링크와 전체보기, 게임은 다른 게임과 전체보기 링크를 제공한다.
2. 자동 발견을 유지할 페이지: 홈, 주요 서비스/기록 허브, 소개·연락처·정책 페이지. 정책 페이지는 검색 유입보다 서비스 신뢰와 탐색 목적이다.
3. 반복성·추가 검토 페이지: 로또 회차별 기록 및 기존 독립 페이지. 현재 기록 허브에 연결된 100회는 당첨번호·추첨일·당첨금이 달라 사이트맵에 유지한다. 현재 허브에서 빠진 오래된 회차(현재 1140회)는 사이트맵에서 제외한다. `yasun.html`(외부 실시간 위젯 중심), `skhynix-split-analysis.html`(기존 시점의 독립 분석 글)은 허브 연결과 콘텐츠 유지 기준을 검토하기 전까지 사이트맵에서 제외한다. 삭제나 noindex는 적용하지 않는다.

Google/Naver 인증 파일은 생성기 입력에서 제외하며 절대 수정하지 않는다. 전체 URL별 분류는 `url-inventory.md`를 참고한다.

## 생성 순서와 소유권

`cleanup_empty_seo.py` → `seo_static.py` → `enhance_detail_seo.py` → `crawl_structure.py` → `generate_sitemap.py` → `validate_crawl.py`.

- `seo_static.py`: 데이터 기반 SEO_STATIC 영역만 관리한다.
- `enhance_detail_seo.py`: 기존 21개 계산기와 3개 게임의 설명 문구만 관리한다. 현재 저장소에는 `enhance_indexable_pages.py`가 없다.
- `crawl_structure.py`: 기존 허브 카드를 보존하고 새 계산기 카드를 추가한다. CRAWL_LINKS 영역의 정적 관련 링크와 증시/아파트의 관련 계산기 링크를 관리한다.
- `calculator/theme.js`: 테마·헤더는 유지하며 정적 관련 링크가 있으면 기존 JS 관련 링크를 중복 삽입하지 않는다.
- `seo_catalog.py`: 공개 URL 정규화, noindex/redirect/canonical 제외 정책 및 주제별 관련 계산기 선택을 공유한다.
- 두 사이트맵/SEO workflow는 기존 공통 concurrency 그룹을 유지한다. 사이트맵 전용 workflow는 HTML을 수정하지 않는다. SEO workflow는 HTML 추가/변경에도 동작하며 생성 링크와 사이트맵을 함께 검증한다.

새 계산기는 `calculator/*.html`에 공개 HTML을 추가하면 발견된다. title/description과 자기 자신을 가리키는 canonical을 권장하며 noindex나 다른 canonical을 지정한 페이지는 허브 및 사이트맵에서 제외한다. 기존 카드의 디자인·문구·순서는 보존하고 새 카드는 같은 CSS 클래스로 추가한다. 새 계산기의 설명 문구와 계산 정확성 검토는 자동 생성하지 않으므로 별도 작성해야 한다. 필요하면 `seo_catalog.py`의 GROUPS에 주제 그룹을 추가한다. 새 게임도 `games/*/index.html`에서 발견되며 기존 카드가 없으면 정적 링크로 연결된다.

## lastmod

파일 시스템 mtime은 사용하지 않는다. Git의 해당 HTML 마지막 커밋 날짜를 UTC로 기록한다. 계산기는 공통 theme.js/theme.css 변경도 반영한다. 생성 직후 미커밋 변경은 생성 당일 UTC 날짜를 사용한다. Git 기록이 없거나 shallow checkout이면 정확하지 않은 날짜를 만들어 넣지 않고 lastmod를 생략한다. 관련 workflow는 전체 이력을 checkout한다.

동일 입력 재실행 시 HTML과 사이트맵이 같도록 빈 줄 누적 및 불필요한 재작성을 방지한다. 동적 데이터가 실제로 변경되면 해당 허브만 새 날짜를 갖는다. 과거 Git에 기록된 의미 없는 변경을 소급 판별하지는 않는다.

Google은 priority/changefreq를 무시하므로 추가하지 않는다. 사이트맵 제출은 크롤링 힌트이며 즉시 크롤링/색인을 보장하지 않는다. 사이트맵 제외도 색인 삭제 지시가 아니다.

근거: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap

## 검증

`python -m unittest discover -s tests -v`: 새 계산기 자동 반영, noindex/인증/redirect/canonical 제외, URL 인코딩, Git 날짜 및 생성 반복 안정성.

`python validate_crawl.py`: 전체 사이트맵 URL 집합·중복·정적 도달성, 생성 링크의 대상, 계산기/게임 두 번 이내 도달, 관련 링크 중복을 검사한다. 실제 Search Console 색인 여부나 운영 서버 HTTP 응답은 이 검증의 범위가 아니다.
