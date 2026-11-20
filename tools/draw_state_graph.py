"""畫出「製作教學簡報」的狀態圖（AGENTS.md 7.5），輸出 SVG，並用 Edge 無介面模式轉成 PNG。
用法：python -X utf8 tools/draw_state_graph.py .
產出：slides/docs/state-graph.svg、slides/docs/state-graph.png
流程有修改時，請同步修改本檔的 ROWS、LOOPS 與 AGENTS.md 7.5。"""
import sys, pathlib, subprocess, html

root = pathlib.Path(sys.argv[1]).resolve()
out = root / 'slides' / 'docs'
out.mkdir(parents=True, exist_ok=True)

# (代號, 類型, 標題, 產物或說明)  類型：node 節點、check 自動檢查、gate 人工關卡
ROWS = [
    ('N0', 'node',  '需求規格',       'brief.md'),
    ('G0', 'gate',  '人：確認規格',   '通過才往下'),
    ('N1', 'node',  '取材（只讀 wiki）', 'source_pack.json'),
    ('C1', 'check', '檢查取材',       'reports/C1.json'),
    ('N2', 'node',  '大綱',           'outline.json ＋ outline.md'),
    ('C2', 'check', '檢查大綱',       'reports/C2.json'),
    ('G1', 'gate',  '人：確認大綱',   '回報被移除的頁面'),
    ('N3', 'node',  '組裝 HTML',      'slides/index.html'),
    ('C3', 'check', '檢查投影片',     'reports/C3.json ＋ 截圖'),
    ('G2', 'gate',  '人：試用',       '自己操作一次'),
    ('N4', 'node',  '發佈紀錄',       'git commit ＋ log'),
]
# 退回：(從, 到, 側邊)  right = 自動檢查退回、left = 人工修改
LOOPS = [('C1', 'N1', 'right'), ('C2', 'N2', 'right'), ('C3', 'N3', 'right'),
         ('G0', 'N0', 'left'), ('G1', 'N2', 'left'), ('G2', 'N3', 'left')]

W, TOP, STEP, BH, BW, CX = 1240, 150, 86, 56, 330, 470
COL = {'node': ('#E8F1FB', '#2B6CB0'), 'check': ('#FFF4E5', '#C05621'), 'gate': ('#EDF7ED', '#2F855A')}
ICON = {'node': '■', 'check': '○', 'gate': '◆'}
y = {r[0]: TOP + i * STEP for i, r in enumerate(ROWS)}
H = TOP + (len(ROWS) - 1) * STEP + 170
e = html.escape
s = []
s.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         'font-family="Microsoft JhengHei, Noto Sans TC, sans-serif">')
s.append('''<defs>
<marker id="a" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#4A5568"/></marker>
<marker id="ao" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#C05621"/></marker>
<marker id="ag" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#2F855A"/></marker>
</defs>''')
s.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
s.append(f'<text x="{CX}" y="50" text-anchor="middle" font-size="28" font-weight="700" fill="#1A202C">製作教學簡報：狀態圖</text>')
s.append(f'<text x="{CX}" y="84" text-anchor="middle" font-size="16" fill="#4A5568">資料來源只有 wiki ・ 投影片只由大綱產生</text>')

# 主線箭頭
for (a, *_), (b, *_) in zip(ROWS, ROWS[1:]):
    s.append(f'<line x1="{CX}" y1="{y[a] + BH/2}" x2="{CX}" y2="{y[b] - BH/2 - 2}" stroke="#4A5568" stroke-width="2" marker-end="url(#a)"/>')
    if a[0] in 'CG':
        s.append(f'<text x="{CX + 8}" y="{(y[a] + y[b]) / 2 + 5}" font-size="13" fill="#4A5568">通過</text>')

# 退回迴圈
for frm, to, side in LOOPS:
    color, mk = ('#C05621', 'ao') if side == 'right' else ('#2F855A', 'ag')
    x0 = CX + BW / 2 if side == 'right' else CX - BW / 2
    xs = x0 + 40 if side == 'right' else x0 - 40
    s.append(f'<path d="M{x0},{y[frm]} H{xs} V{y[to]} H{x0 + (2 if side == "right" else -2)}" fill="none" '
             f'stroke="{color}" stroke-width="2" stroke-dasharray="6 4" marker-end="url(#{mk})"/>')
    label = '不通過 ≤3 次' if side == 'right' else '修改意見'
    lx = xs + 6 if side == 'right' else xs - 6
    anchor = 'start' if side == 'right' else 'end'
    s.append(f'<text x="{lx}" y="{(y[frm] + y[to]) / 2 + 5}" font-size="13" fill="{color}" text-anchor="{anchor}">{label}</text>')

# 方塊
for code, kind, title, sub in ROWS:
    fill, stroke = COL[kind]
    x, top = CX - BW / 2, y[code] - BH / 2
    rx = 28 if kind == 'gate' else (6 if kind == 'node' else 16)
    s.append(f'<rect x="{x}" y="{top}" width="{BW}" height="{BH}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    s.append(f'<text x="{x + 14}" y="{y[code] - 4}" font-size="17" font-weight="700" fill="{stroke}">{ICON[kind]} {code}</text>')
    s.append(f'<text x="{x + 74}" y="{y[code] - 4}" font-size="17" font-weight="700" fill="#1A202C">{e(title)}</text>')
    s.append(f'<text x="{x + 74}" y="{y[code] + 18}" font-size="13" fill="#4A5568">{e(sub)}</text>')

# 右側說明卡
def card(x, top, w, title, lines, stroke):
    h = 34 + 22 * len(lines)
    s.append(f'<rect x="{x}" y="{top}" width="{w}" height="{h}" rx="8" fill="#FFFFFF" stroke="{stroke}" stroke-width="1.5"/>')
    s.append(f'<text x="{x + 14}" y="{top + 24}" font-size="15" font-weight="700" fill="{stroke}">{e(title)}</text>')
    for i, l in enumerate(lines):
        s.append(f'<text x="{x + 14}" y="{top + 48 + 22 * i}" font-size="13" fill="#2D3748">{e(l)}</text>')
NX, NW = 800, 410
card(NX, y['N1'] - 30, NW, '資料不足的頁面', ['wiki 裡找不到足夠來源的投影片：', '自動從大綱移除、記入 removed_nodes，', '在下一個人工關卡（G1）一併報告。', '不可以用自己的知識補內容。'], '#9B2C2C')
card(NX, y['N2'] + 52, NW, '剎車機制', ['每個自動檢查最多退回 3 次；', '第 3 次仍不通過 → 停下，交給人處理。', '人工修改不計入，修改後次數重新計算。'], '#C05621')
card(NX, y['G1'] - 10, NW, '每頁投影片（新人自學，不放圖）', ['位置、學習目標、重點（附條號）、', '一題單選自我檢查（點選後顯示對錯、', '解說和條號連結）、導覽。題目和答案', '都要對得到 wiki；不記錄學員進度。'], '#2B6CB0')
card(NX, y['C3'] + 60, NW, '檢查方式', ['程式：條號、連結、字數、頁數、截圖', '獨立審查：另一個 agent 只看產物，', '判斷內容是否忠於 wiki、是否看得懂'], '#4A5568')

# 圖例與 wiki 更新
ly = H - 60
items = [('node', '節點（產生產物）'), ('check', '自動檢查'), ('gate', '人工確認關卡')]
for i, (k, t) in enumerate(items):
    fill, stroke = COL[k]
    lx = 40 + i * 210
    s.append(f'<rect x="{lx}" y="{ly}" width="26" height="18" rx="4" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    s.append(f'<text x="{lx + 34}" y="{ly + 14}" font-size="14" fill="#2D3748">{t}</text>')
s.append(f'<text x="{40}" y="{ly + 44}" font-size="13" fill="#4A5568">wiki 更新時：比對 source_pack 記錄的來源頁雜湊，有變動就從 N1 重跑，下游產物標為過期。</text>')
s.append('</svg>')

svg = '\n'.join(s)
(out / 'state-graph.svg').write_text(svg, encoding='utf-8', newline='\n')
page = out / '_render.html'
page.write_text(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}}</style>{svg}', encoding='utf-8')
edge = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
subprocess.run([edge, '--headless', '--disable-gpu', '--hide-scrollbars', f'--window-size={W},{H}',
                f'--screenshot={out / "state-graph.png"}', page.as_uri()], check=True, capture_output=True, timeout=60)
page.unlink()
print('saved', out / 'state-graph.svg', out / 'state-graph.png')
