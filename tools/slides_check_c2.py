"""簡報 C2：檢查大綱（slides/outline.json），程式部分。
用法：python -X utf8 tools/slides_check_c2.py .
檢查項目（依 brief 與 AGENTS.md 7.5）：
- 結構：主線從 open 依序到 end；每個節點都在主線或被主線節點 related 連到；related 目標存在。
- 每頁格式：學習目標 ≤30 字；重點 3～5 點、每點 ≤40 字、每點都有事實；自我檢查 3～4 個選項、答案索引有效、有解說和事實。
- 可追溯：所有事實編號都存在於 source_pack。
- 數字：重點、正確選項、解說裡的數字，都要出現在所引用事實的原文裡（中文數字和阿拉伯數字視為相同）。
- C1 warn 的事實：不可用在重點、自我檢查和圖（不可自行補寫例外，因為例外內容不在 wiki）。
- 主線每張圖都要列出依據事實（diagram.facts），圖構想裡的數字要在這些事實中。
- 開場頁免責聲明要和 wiki 首頁原文相同。
- 欄位白名單：每個節點只能有 brief 規定的欄位（brief 修訂後拿掉學姊，頁面上不可放 6 個區塊以外的文字）。
- 資料不足：主線或延伸節點的頁面若不在 source_pack，列入 removed_nodes（應由 N2 處理）。
結果寫入 slides/reports/C2.json：history 記錄每次執行的結果；退回次數＝程式不通過次數＋獨立審查不通過次數。
另外產生 slides/outline.md（給人審閱，也是獨立審查的輸入）。"""
import sys, re, json, pathlib

root = pathlib.Path(sys.argv[1]).resolve()
pack = json.loads((root / 'slides/source_pack.json').read_text(encoding='utf-8'))
ol = json.loads((root / 'slides/outline.json').read_text(encoding='utf-8'))
LIM = {'goal': 30, 'point': 40}
BASE = {'id', 'kind', 'title', 'goal'}
ALLOWED = {'open': BASE | {'info', 'disclaimer', 'disclaimer_text'}, 'end': BASE | {'info', 'more_wiki'},
           'main': BASE | {'chapter', 'page', 'points', 'diagram', 'quiz', 'related'}, 'ext': BASE | {'page', 'points', 'quiz', 'related'}}
CN = {'零': 0, '一': 1, '二': 2, '兩': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}

def cn2int(s):
    total, sec, num = 0, 0, 0
    for ch in s:
        if ch in CN: num = CN[ch]
        elif ch == '十': sec += (num or 1) * 10; num = 0
        elif ch == '百': sec += (num or 1) * 100; num = 0
        elif ch == '千': sec += (num or 1) * 1000; num = 0
        elif ch == '萬': total += (sec + num) * 10000; sec = num = 0
    return total + sec + num

UNIT = r'(?=\s*(?:%|年|公尺|公分|伏特|小時|倍|人|度|公升|公斤|毫升|分貝|條|類|種|項|日|月|週|次|元|萬))'
def numbers(text):
    out = set(re.findall(r'\d+(?:\.\d+)?', text))
    for m in re.finditer(r'[零一二兩三四五六七八九十百千萬]+' + UNIT, text):
        out.add(str(cn2int(m.group())))
    for m in re.finditer(r'百分之([零一二三四五六七八九十百]+)', text):
        out.add(str(cn2int(m[1])))
    return out

facts = {f['id']: f for p in pack['pages'].values() for f in p['facts']}
def resolve(node, refs):
    ids = []
    for r in refs:
        ids.append(r if isinstance(r, str) and '#' in r else f"{node['page']}#{r}")
    return ids

nodes = {n['id']: n for n in ol['nodes']}
errors, warns, removed = [], [], list(ol['meta'].get('removed_nodes', []))
def err(nid, msg): errors.append({'node': nid, 'msg': msg})

# 結構
mp = ol['main_path']
if mp[0] != 'open' or mp[-1] != 'end': err('-', '主線要從 open 開始、到 end 結束')
for nid in mp:
    if nid not in nodes: err(nid, '主線節點不存在')
reach = set(mp)
for nid in mp:
    for r in nodes.get(nid, {}).get('related', []):
        if r not in nodes: err(nid, f'related 目標不存在：{r}')
        reach.add(r)
for nid in nodes:
    if nid not in reach: err(nid, '沒有在主線上，也沒有被主線節點連到')

if nodes.get('open', {}).get('disclaimer_text') != pack.get('disclaimer'):
    err('open', '開場頁的免責聲明要和 wiki 首頁原文完全相同')
for nid, n in nodes.items():
    if len(n.get('goal', '')) > LIM['goal']: err(nid, f"學習目標超過 {LIM['goal']} 字（{len(n['goal'])}）")
    extra_keys = set(n) - ALLOWED[n['kind']]
    if extra_keys: err(nid, f'有 brief 沒有規定的欄位（頁面上不可放 6 個區塊以外的文字）：{sorted(extra_keys)}')
    if n['kind'] in ('open', 'end'):
        continue
    if n['page'] not in pack['pages']:
        removed.append({'node': nid, 'reason': 'source_pack 沒有此頁'}); continue
    pts = n.get('points', [])
    if not 3 <= len(pts) <= 5: err(nid, f'重點要 3～5 點（目前 {len(pts)}）')
    for i, p in enumerate(pts, 1):
        if len(p['text']) > LIM['point']: err(nid, f"重點 {i} 超過 {LIM['point']} 字（{len(p['text'])}）：{p['text']}")
        ids = resolve(n, p.get('facts', []))
        if not ids: err(nid, f'重點 {i} 沒有引用事實'); continue
        miss = [x for x in ids if x not in facts]
        if miss: err(nid, f'重點 {i} 的事實不存在：{miss}'); continue
        src = ''.join(facts[x]['text'] for x in ids)
        extra = numbers(p['text']) - numbers(src)
        if extra: err(nid, f"重點 {i} 的數字 {sorted(extra)} 不在所引事實中：{p['text']}")
        flagged = [x for x in ids if 'review' in facts[x]]
        if flagged:
            err(nid, f'重點 {i} 用到 C1 warn 事實 {flagged}（規則：warn 事實不可使用；不可自行補寫例外）')
    if n['kind'] == 'main':
        dgm = n.get('diagram') or {}
        ids = resolve(n, dgm.get('facts', []))
        miss = [x for x in ids if x not in facts]
        if not ids or miss: err(nid, f'圖沒有列出依據事實，或事實不存在：{miss}')
        else:
            if [x for x in ids if 'review' in facts[x]]: err(nid, '圖用到 C1 warn 事實')
            extra = numbers(dgm.get('idea', '')) - numbers(''.join(facts[x]['text'] for x in ids))
            if extra: err(nid, f'圖構想的數字 {sorted(extra)} 不在圖的依據事實中')
    q = n.get('quiz')
    if not q: err(nid, '沒有自我檢查'); continue
    if not 3 <= len(q['options']) <= 4: err(nid, '自我檢查選項要 3～4 個')
    if not 0 <= q['answer'] < len(q['options']): err(nid, '答案索引無效')
    if not q.get('explain'): err(nid, '自我檢查沒有解說')
    ids = resolve(n, q.get('facts', []))
    miss = [x for x in ids if x not in facts]
    if not ids or miss: err(nid, f'自我檢查事實不存在或為空：{miss}'); continue
    flagged = [x for x in ids if 'review' in facts[x]]
    if flagged: err(nid, f'自我檢查用到 C1 warn 事實 {flagged}（規則：warn 事實不可出題）')
    src = ''.join(facts[x]['text'] for x in ids)
    for label, txt in (('正確選項', q['options'][q['answer']]), ('解說', q['explain'])):
        extra = numbers(txt) - numbers(src)
        if extra: err(nid, f'{label}的數字 {sorted(extra)} 不在所引事實中：{txt}')
    if len(set(q['options'])) != len(q['options']): err(nid, '選項重複')

main_n = sum(1 for n in nodes.values() if n['kind'] == 'main')
ext_n = sum(1 for n in nodes.values() if n['kind'] == 'ext')
if main_n + ext_n + 2 > 27: err('-', f'頁數超過 27（主線 {main_n}＋延伸 {ext_n}＋開場結尾 2）')

rep = root / 'slides/reports/C2.json'
prev = json.loads(rep.read_text(encoding='utf-8')) if rep.exists() else {}
history = prev.get('history', []) + ['pass' if not errors else 'fail']
attempt = len(history)
# 退回次數只算「不通過」的執行（重跑但通過不算）；獨立審查的不通過由製作者另外記入 review_rejections
result = {'check': 'C2', 'attempt': attempt, 'history': history,
          'rejections': history.count('fail') + prev.get('review_rejections', 0),
          'review_rejections': prev.get('review_rejections', 0), 'max_rejections': 3,
          'program': {'pass': not errors, 'errors': errors, 'removed_nodes': removed},
          'counts': {'main': main_n, 'ext': ext_n}, 'review': None}
rep.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')

# outline.md：給人審閱，每個重點後面附上所引事實原文
L = [f"# 大綱：{ol['meta']['title']}", '', '> 由 outline.json 自動產生。每個重點下方的「依據」是 source_pack 裡的 wiki 原句。', '']
L.append('**主線**：' + ' → '.join(nodes[x]['title'] if x in nodes else x for x in mp)); L.append('')
if removed: L += ['**資料不足而移除的頁面**：' + '、'.join(f"{r['node']}（{r['reason']}）" for r in removed), '']
for nid in mp + [x for x in nodes if x not in mp]:
    n = nodes[nid]
    tag = {'open': '開場', 'end': '結尾', 'main': '主線', 'ext': '延伸'}[n['kind']]
    L += [f"## [{tag}] {nid}｜{n['title']}", '', f"- **學習目標**：讀完這頁，你可以{n['goal']}"]
    for x in n.get('info', []): L.append(f'- {x}')
    for i, p in enumerate(n.get('points', []), 1):
        L.append(f"- **重點 {i}**：{p['text']}")
        for x in resolve(n, p['facts']):
            f = facts.get(x)
            if f: L.append(f"  - 依據 `{x}`{' ⚠' if 'review' in f else ''}：{f['text']}（{'、'.join(c['law'] + ' §' + c['no'] for c in f['cites'])}）")
    if n.get('disclaimer_text'): L.append(f"- **免責聲明**：{n['disclaimer_text']}")
    if n.get('diagram'):
        L.append(f"- **圖**（{n['diagram']['type']}）：{n['diagram']['idea']}")
        for x in resolve(n, n['diagram'].get('facts', [])):
            f = facts.get(x)
            if f: L.append(f"  - 圖的依據 `{x}`：{f['text']}")
    if n.get('quiz'):
        q = n['quiz']
        L.append(f"- **自我檢查**：{q['q']}")
        for i, o in enumerate(q['options']): L.append(f"  - {'✅' if i == q['answer'] else '⬜'} {o}")
        L.append(f"  - 解說：{q['explain']}")
        for x in resolve(n, q['facts']):
            f = facts.get(x)
            if f: L.append(f"  - 依據 `{x}`：{f['text']}")
    if n.get('related'): L.append('- **連到**：' + '、'.join(nodes[r]['title'] for r in n['related'] if r in nodes))
    if n.get('more_wiki'): L.append('- **延伸學習地圖（只列 wiki 連結）**：' + '、'.join(n['more_wiki']))
    L.append('')
(root / 'slides/outline.md').write_text('\n'.join(L), encoding='utf-8', newline='\n')
print(json.dumps({k: result[k] for k in ('attempt', 'rejections', 'program', 'counts')}, ensure_ascii=False, indent=1))
