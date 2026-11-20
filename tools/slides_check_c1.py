"""簡報 C1：檢查取材（slides/source_pack.json）。
用法：python -X utf8 tools/slides_check_c1.py .
程式檢查：
- brief 列出的頁面都有取到；每筆事實的條號都在 raw 裡存在。
- 漏抽檢查：沒有條號而被跳過的內容行，只允許是情境描述或跨頁連結。
- 每個投影片節點至少 MIN_FACTS 筆事實；不足的列為 insufficient（依 AGENTS.md 7.5，N2 會自動移除並在 G1 報告）。
另外產生 slides/reports/C1_review_input.json：每筆事實配上所引條文的原文，交給獨立審查 agent。
結果寫入 slides/reports/C1.json，並累計退回次數（attempt）。"""
import sys, re, json, pathlib

MIN_FACTS = 3
root = pathlib.Path(sys.argv[1]).resolve()
rep_dir = root / 'slides/reports'; rep_dir.mkdir(parents=True, exist_ok=True)
pack = json.loads((root / 'slides/source_pack.json').read_text(encoding='utf-8'))

articles = {}
for f in (root / 'raw').glob('*.md'):
    t = f.read_text(encoding='utf-8')
    for m in re.finditer(r'^## 第 (\S+) 條（.*?）\n\n(.*?)(?=\n\n---)', t, re.M | re.S):
        articles[(f.stem, m[1])] = m[2]

errors, insufficient, review = [], [], []
if pack['missing_pages']:
    errors.append({'type': 'missing_page', 'pages': pack['missing_pages']})
for name, pg in pack['pages'].items():
    if len(pg['facts']) < MIN_FACTS:
        insufficient.append({'page': name, 'facts': len(pg['facts'])})
    for f in pg['facts']:
        texts = {}
        for c in f['cites']:
            k = (c['law'], c['no'])
            if k not in articles:
                errors.append({'type': 'cite_not_found', 'fact': f['id'], 'cite': f"{c['law']} §{c['no']}"})
            else:
                texts[f"{c['law']} §{c['no']}"] = articles[k]
        review.append({'id': f['id'], 'text': f['text'], 'inherited': f['inherited'], 'articles': texts})
CONTEXT_SECTIONS = ('什麼時候會遇到',)
XREF = ('見 ', '請看', '詳見')
WIKI_PAGES = {q.stem for q in (root / 'wiki').rglob('*.md')}
for name, pg in pack['pages'].items():
    for u in pg.get('uncited', []):
        tail = u['text'].split('：')[-1].strip()
        if u['section'] in CONTEXT_SECTIONS or any(x in u['text'] for x in XREF) or tail in WIKI_PAGES:
            continue  # 情境描述與跨頁連結不是法規事實，允許沒有條號
        errors.append({'type': 'uncited_content', 'page': name, 'section': u['section'], 'text': u['text']})
if not pack.get('disclaimer'):
    errors.append({'type': 'missing_disclaimer'})

prev = rep_dir / 'C1.json'
attempt = json.loads(prev.read_text(encoding='utf-8')).get('attempt', 0) + 1 if prev.exists() else 1
result = {'check': 'C1', 'attempt': attempt, 'max_attempts': 3,
          'facts': sum(len(p['facts']) for p in pack['pages'].values()),
          'program': {'pass': not errors, 'errors': errors, 'insufficient': insufficient},
          'review': None}
prev.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')
(rep_dir / 'C1_review_input.json').write_text(json.dumps(review, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')
print(json.dumps({k: v for k, v in result.items() if k != 'review'}, ensure_ascii=False, indent=1))
