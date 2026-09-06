from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
DATA = ROOT / "lotto" / "data" / "results.json"


def fmt_date(value: str) -> str:
    return str(value or "").replace("-", ".")


def fmt_approx_eok(won) -> str:
    try:
        eok = float(won) / 100_000_000
        return f"약 {eok:.1f}억원"
    except Exception:
        return "-"


def build_card(latest: dict) -> str:
    draw = int(latest.get("draw") or 0)
    date = fmt_date(latest.get("date"))
    numbers = latest.get("numbers") or []
    bonus = latest.get("bonus")
    winners = int(latest.get("first_winners") or 0)
    prize = fmt_approx_eok(latest.get("first_prize"))

    balls = "".join(f'<span class="ball">{int(n)}</span>' for n in numbers)
    if bonus is not None:
        balls += f'<span class="ball bonus">{int(bonus)}</span>'

    return f'''<div class="card lotto">
        <div class="lotto-top">
          <div><h3>{draw}회 당첨번호</h3><small>{date} 추첨</small></div>
          <strong>1등 {winners}명</strong>
        </div>
        <div class="balls">
          {balls}
        </div>
        <div class="lotto-bottom"><span>1등 당첨금</span><strong>{prize}</strong></div>
      </div>'''


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    latest = data.get("latest") or {}
    if not latest.get("draw"):
        raise SystemExit("latest lotto data is missing")

    html = INDEX.read_text(encoding="utf-8")
    pattern = re.compile(
        r'<div class="card lotto">.*?<div class="lotto-bottom">.*?</div>\s*</div>',
        re.S,
    )
    replacement = build_card(latest)
    updated, count = pattern.subn(replacement, html, count=1)
    if count != 1:
        raise SystemExit(f"homepage lotto card match failed: {count}")

    if updated == html:
        print("Homepage lotto card already up to date")
        return

    INDEX.write_text(updated, encoding="utf-8")
    print(f"Homepage lotto card updated to draw {latest.get('draw')}")


if __name__ == "__main__":
    main()
