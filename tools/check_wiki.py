"""wiki 自我檢查（AGENTS.md 7.4 與 Lint 用）。
檢查：連結目標存在、條號錨點對得到 raw 標題、顯示文字格式、提示框語法、
frontmatter sources 和內文引用一致、孤兒頁、殘留的 [[ ]] 語法。
用法：python -X utf8 tools/check_wiki.py .   最後一行印出 OK 或 ERRORS。"""
import re, sys, pathlib, os, unicodedata, urllib.parse
root = pathlib.Path(sys.argv[1]).resolve()
def slug(h):
    s = ''.join(c for c in h.lower() if c in '-_ ' or unicodedata.category(c)[0] in 'LNM')
    return s.replace(' ', '-')
anchors = {}
for f in root.rglob('*.md'):
    if '.git' in f.parts: continue
    anchors[f.resolve()] = {slug(h) for h in re.findall(r'^#+ (.+)$', f.read_text(encoding='utf-8'), re.M)}
ok = True; inbound = {}
for p in (root/'wiki').rglob('*.md'):
    t = p.read_text(encoding='utf-8')
    if '[[' in re.sub(r'`[^`]*`', '', t): print('WIKILINK LEFT', p.name); ok=False
    for bad in re.findall(r'^> \[!(?!TIP\]$|WARNING\]$|IMPORTANT\]$).*$', t, re.M): print('BAD ALERT', p.name, bad); ok=False
    cited = {}
    for disp, href in re.findall(r'(?<!!)\[([^\]]+)\]\(([^)\s]+)\)', t):
        if href.startswith('http'): continue
        path, _, frag = urllib.parse.unquote(href).partition('#')
        tgt = (p.parent/path).resolve()
        if tgt not in anchors: print('DEAD', p.name, href); ok=False; continue
        if frag and frag not in anchors[tgt]: print('BADANCHOR', p.name, href); ok=False
        if tgt.parent.name == 'raw' and frag:
            m = re.fullmatch(r'(\S+) §([\d-]+)', disp)
            if not m or m[1] != tgt.stem or not frag.startswith(f'第-{m[2]}-條'): print('BADDISP', p.name, disp, href); ok=False
            else: cited.setdefault(m[1], set()).add(m[2])
        if tgt.is_relative_to(root/'wiki') and tgt != p.resolve(): inbound[tgt.stem] = inbound.get(tgt.stem,0)+1
    if t.startswith('---'):
        fm = {law:{n.strip() for n in nos.split(',')} for law, nos in re.findall(r'^\s+- (\S+): \[([^\]]*)\]', t.split('---')[1], re.M)}
        for law in set(fm)|set(cited):
            if fm.get(law,set()) != cited.get(law,set()): print('FM-MISMATCH', p.name, law, sorted(fm.get(law,set())-cited.get(law,set())), sorted(cited.get(law,set())-fm.get(law,set()))); ok=False
orph = [p.stem for p in (root/'wiki').rglob('*.md') if p.stem not in ('index','log') and not inbound.get(p.stem)]
print('ORPHANS', orph); print('OK' if ok and not orph else 'ERRORS')
