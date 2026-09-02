from pathlib import Path

p = Path('index.html')
s = p.read_text(encoding='utf-8')
repl = {
    '/calculator/salary/': '/calculator/salary.html',
    '/calculator/stock-return/': '/calculator/stock-return.html',
    '/calculator/average-price/': '/calculator/average-price.html',
    '/calculator/loan/': '/calculator/loan.html',
}
for old, new in repl.items():
    s = s.replace(old, new)
p.write_text(s, encoding='utf-8')
print('fixed live homepage calculator links - trigger')
