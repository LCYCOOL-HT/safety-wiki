"""簡報 N1：從 wiki 情境頁抽出事實，產生 slides/source_pack.json。
用法：python -X utf8 tools/slides_extract.py .
規則（AGENTS.md 7.5）：
- 只讀 wiki；事實就是 wiki 原句（去掉連結語法），不改寫。
- 一行有條號連結＝一筆事實；沒有條號的條列項目、表格列，繼承所在小標題的條號（標記 inherited）。
- 「補充說明」（> [!TIP]）不是法規事實，排除；「待確認」（> [!WARNING]）記為 caveats。
- 每頁記錄內容雜湊，供 wiki 更新時判斷是否過期。"""
import sys, re, json, hashlib, pathlib, datetime

root = pathlib.Path(sys.argv[1]).resolve()
brief = (root / 'slides/brief.md').read_text(encoding='utf-8')
# brief 裡提到的情境頁（「情境/xxx」）
pages = list(dict.fromkeys(re.findall(r'情境/([^\s|｜`]+)', brief)))
pages += [p for p in re.findall(r'^\| ([^|\n]+?) \| \d+ \|$', brief, re.M) if p not in pages]  # 延伸節點表

LINK = re.compile(r'\[([^\]]+)\]\(([^)\s]+)\)')
CITE = re.compile(r'\[([^\]]+?) §([\d-]+)\]\((?:\.\./)+raw/([^)#]+)\.md#([^)]+)\)')

def clean(s):
    s = LINK.sub(lambda m: m[1], s)
    s = re.sub(r'\*\*|`', '', s)
    s = re.sub(r'^\s*(?:[-*]|\d+\.)\s*(?:\[ \]\s*)?', '', s)
    s = s.replace('❌', '').strip()
    if s.startswith('|'):
        cells = [c.strip() for c in s.strip('|').split('|')]
        s = '｜'.join(c for c in cells if c)
    return s.strip(' ：')

def cites_of(s):
    return [{'law': m[3], 'no': m[2], 'anchor': m[4]} for m in CITE.finditer(s)]

out = {'generated': datetime.date.today().isoformat(), 'source': 'wiki/情境', 'pages': {}, 'missing_pages': []}
for name in pages:
    p = root / 'wiki/情境' / f'{name}.md'
    if not p.exists():
        out['missing_pages'].append(name); continue
    text = p.read_text(encoding='utf-8')
    body = text.split('\n---\n', 1)[1] if text.startswith('---') else text
    facts, caveats, uncited = [], [], []
    section, sec_cites, block, intro_cites = '', [], None, []
    for line in body.splitlines():
        if line.startswith('#'):
            section = clean(re.sub(r'^#+\s*', '', CITE.sub('', line)))
            sec_cites = cites_of(line)
            intro_cites = []
            block = None
            if line.startswith('## 涉及法規') or line.startswith('## 相關情境'):
                section = '__skip__'
            continue
        if section == '__skip__' or not line.strip() or line.startswith('[🏠') or line.strip() == '---':
            continue
        if line.startswith('> [!'):
            block = line[4:].split(']')[0]; continue
        if line.startswith('>'):
            inner = line.lstrip('> ').strip()
            if block == 'TIP' or not inner or inner.startswith('**'):
                continue
            if block == 'WARNING':
                caveats.append(clean(inner)); continue
            if block == 'IMPORTANT' and not cites_of(inner):
                continue  # IMPORTANT 裡沒有條號的說明（例如表格導覽）不當事實
            line = inner
        else:
            block = None
        if re.match(r'^\|[-| ]+\|$', line) or (line.startswith('|') and '---' in line):
            continue
        c = cites_of(line)
        inherited = False
        is_item = line.lstrip().startswith(('-', '|')) or re.match(r'^\s*\d+\.', line)
        if not c:
            # 條列項目沒有條號時：先繼承前面以「：」結尾的引言句，再繼承小標題
            src = intro_cites if is_item and intro_cites else sec_cites
            if src:
                c, inherited = src, True
            else:
                t0 = clean(line)
                if t0 and not line.startswith('|'):
                    uncited.append({'section': section, 'text': t0})
                continue
        ends_colon = CITE.sub('', line).rstrip().endswith(('：', ':'))
        if ends_colon:
            intro_cites = c
        elif not is_item or not line.startswith((' ', '	')):
            intro_cites = [] if not is_item else intro_cites
        t = clean(CITE.sub('', line))
        t = re.sub(r'[（(]\s*[)）]', '', t)
        t = re.sub(r'\s+([）)，。、；：])', r'\1', t).strip(' 、，。；')
        if not t or (line.startswith('|') and t.startswith(('項目｜', '類型｜', '種類｜', '情形｜', '危害｜', '空間裡'))):
            continue
        facts.append({'id': f'{name}#{len(facts) + 1}', 'section': section, 'text': t,
                      'cites': [{'law': x['law'], 'no': x['no']} for x in c], 'inherited': inherited})
    out['pages'][name] = {'path': f'wiki/情境/{name}.md',
                          'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                          'facts': facts, 'caveats': caveats, 'uncited': uncited}

idx = (root / 'wiki/index.md').read_text(encoding='utf-8')
m = re.search(r'^> (本 Wiki .+)$', idx, re.M)
out['disclaimer'] = m[1] if m else None
(root / 'slides/source_pack.json').write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8', newline='\n')
n = sum(len(v['facts']) for v in out['pages'].values())
print(f'pages {len(out["pages"])}, facts {n}, missing {out["missing_pages"]}')
for k, v in out['pages'].items():
    print(f'  {len(v["facts"]):3d} {k}' + (f'  caveats {len(v["caveats"])}' if v['caveats'] else ''))
