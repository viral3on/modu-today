from pathlib import Path

p = Path('seo_static.py')
text = p.read_text(encoding='utf-8')
text = text.replace("name=r.get('apt_name') or r.get('apartment') or r.get('name') or r.get('아파트') or '아파트'", "name=r.get('apt') or r.get('apt_name') or r.get('apartment') or r.get('name') or r.get('아파트') or '아파트'")
text = text.replace("price=r.get('deal_amount') or r.get('price') or r.get('거래금액') or 0", "price=r.get('price_manwon') or r.get('deal_amount') or r.get('price') or r.get('거래금액') or 0")
p.write_text(text, encoding='utf-8')
print('patched apartment SEO field mapping')
