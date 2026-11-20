"""把 wiki 頁面裡的簡寫標記展開成 GitHub 標準 Markdown 連結。
  {法規名§條號}   → [法規名 §條號](../../raw/法規名.md#GitHub錨點)
  {{頁面名}}       → [頁面名](相對路徑)
  {{法規/名稱|顯示文字}} → [顯示文字](相對路徑)
用法：python -X utf8 tools/expand_tokens.py .
找不到的條號或頁面會列出來（MISSING / NOPAGE），並保留原標記。"""
import re, sys, pathlib, os, unicodedata
root = pathlib.Path(sys.argv[1]).resolve()
def slug(h):
    s = ''.join(c for c in h.lower() if c in '-_ ' or unicodedata.category(c)[0] in 'LNM')
    return s.replace(' ', '-')
heads = {}
for f in (root/'raw').glob('*.md'):
    for full, no in re.findall(r'^## (第 (\S+) 條（.*?）)$', f.read_text(encoding='utf-8'), re.M):
        heads[(f.stem, no)] = full
pages = {p.stem: p for p in (root/'wiki').rglob('*.md')}
bad = 0
for p in (root/'wiki').rglob('*.md'):
    t = p.read_text(encoding='utf-8'); o = t
    rel = lambda target: pathlib.PurePath(os.path.relpath(target, p.parent)).as_posix()
    def r1(m):
        global bad
        law, no = m[1], m[2]
        if (law, no) not in heads: print('MISSING', p.name, law, no); bad += 1; return m[0]
        return f'[{law} §{no}]({rel(root/"raw"/(law+".md"))}#{slug(heads[(law,no)])})'
    t = re.sub(r'\{([^{}\s§]+)§([\d-]+)\}', r1, t)
    def r2(m):
        global bad
        name, disp = m[1].split('/')[-1], m[2] or m[1]
        if name not in pages: print('NOPAGE', p.name, name); bad += 1; return m[0]
        return f'[{disp}]({rel(pages[name])})'
    t = re.sub(r'\{\{([^{}|]+)(?:\|([^{}]+))?\}\}', r2, t)
    if t != o: p.write_text(t, encoding='utf-8', newline='\n')
print('expand done, problems:', bad)
