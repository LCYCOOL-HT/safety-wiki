"""簡報 C3：檢查投影片（slides/safety_training_deck.html），程式部分。
用法：python -X utf8 tools/slides_check_c3.py .
投影片依大綱與使用者選定的視覺版型製作（AGENTS.md 7.5）。這裡檢查投影片和大綱、raw 是否一致：
- 頁數：封面＋學習地圖（open）＋主線＋總複習（end）＝大綱節點數＋1。
- 每頁對得到大綱：主線頁的標題、「記住這句」都出現在該頁；每個重點至少有一個引用條號出現在該頁。
- 條號連結：每個 data-c 條號都能對到 raw 裡存在的條文標題錨點。
- 不記錄進度：不使用 localStorage／sessionStorage／indexedDB／cookie。
結果寫入 slides/reports/C3.json：history 記錄每次執行的結果；退回次數＝程式不通過次數＋獨立審查不通過次數。"""
import sys, re, json, html, pathlib

root = pathlib.Path(sys.argv[1]).resolve()
ol = json.loads((root / 'slides/outline.json').read_text(encoding='utf-8'))
deck_path = root / ol['meta'].get('deck', 'slides/safety_training_deck.html')
src = deck_path.read_text(encoding='utf-8')
pack = json.loads((root / 'slides/source_pack.json').read_text(encoding='utf-8'))
facts = {f['id']: f for p in pack['pages'].values() for f in p['facts']}
nodes = [n for n in ol['nodes']]
errors = []
def err(where, msg): errors.append({'where': where, 'msg': msg})
flat = lambda s: re.sub(r'\s+', '', html.unescape(re.sub(r'<[^>]+>', '', s)))

# 條號代碼表（從投影片的 LAWS 讀出）
LAWS = {m[1]: m[2] for m in re.finditer(r"'(\S)': \{ file: '([^']+)'", src)}
anchors = {}
for f in (root / 'raw').glob('*.md'):
    for m in re.finditer(r'^## (第 (\S+) 條.*)$', f.read_text(encoding='utf-8'), re.M):
        anchors[(f.stem, m[2])] = re.sub(r'[^\w\- ]', '', m[1].strip().lower()).replace(' ', '-')
chmap = {}
for m in re.finditer(r"'(\S)': \{ file: '[^']+', short: '[^']+', ch: \{([^}]*)\}", src):
    chmap[m[1]] = dict(re.findall(r"'([^']+)': '([^']+)'", m[2]))
for k, law in LAWS.items():
    if not (root / 'raw' / f'{law}.md').exists(): err('cite', f'代碼 {k} 對應的 raw 檔不存在：{law}')

sections = re.findall(r'<section data-title=.*?</section>', src, re.S)
if len(sections) != len(nodes) + 1:
    err('-', f'頁數 {len(sections)} 不等於大綱節點數＋1（{len(nodes) + 1}）')

def sec_cites(s):
    out = set()
    for c in re.findall(r'data-c="([^"]+)"', s):
        k, art = c.split('|')
        law = LAWS.get(k)
        if not law: err('cite', f'未知的法規代碼：{c}'); continue
        want = f"第-{art}-條{chmap.get(k, {}).get(art, '')}"
        if anchors.get((law, art)) != want: err('cite', f'條號錨點對不到 raw：{c} → {want}')
        out.add((law, art))
    return out

for s in sections: sec_cites(s)
mains = [n for n in nodes if n['kind'] == 'main']
for n, s in zip(mains, sections[2:2 + len(mains)]):
    t = flat(s)
    for k in ('title', 'takeaway'):
        if n.get(k) and flat(n[k]) not in t: err(n['id'], f'頁面上找不到大綱的{k}：{n[k]}')
    shown = sec_cites(s)
    for i, p in enumerate(n['points'], 1):  # 一筆事實可能同時引用定義條和主要條；每個重點至少要有一個條號出現在頁面上
        need = {(c['law'], c['no']) for r in p['facts'] for c in facts[r if isinstance(r, str) and '#' in r else f"{n['page']}#{r}"]['cites']}
        if not need & shown: err(n['id'], f'重點 {i} 引用的條號都沒有出現在頁面上：{sorted(need)}')
if re.search(r'localStorage|sessionStorage|indexedDB|document\.cookie', src): err('-', '使用了瀏覽器儲存（規定不記錄進度）')

rep = root / 'slides/reports/C3.json'
prev = json.loads(rep.read_text(encoding='utf-8')) if rep.exists() else {}
history = prev.get('history', []) + ['pass' if not errors else 'fail']
result = {'check': 'C3', 'deck': str(deck_path.relative_to(root)).replace('\\', '/'), 'attempt': len(history), 'history': history,
          'rejections': history.count('fail') + prev.get('review_rejections', 0), 'review_rejections': prev.get('review_rejections', 0),
          'max_rejections': 3, 'slides': len(sections), 'program': {'pass': not errors, 'errors': errors}, 'review': None}
rep.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')
print(json.dumps({k: result[k] for k in ('attempt', 'rejections', 'slides', 'program')}, ensure_ascii=False, indent=1))
