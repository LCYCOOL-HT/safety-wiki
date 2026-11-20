"""依各頁 frontmatter 的 sources 條數，更新 wiki/index.md 裡的「（引用 N 條）」。
用法：python -X utf8 tools/update_index_counts.py ."""
import re, sys, pathlib
root = pathlib.Path(sys.argv[1]); idx = root/'wiki/index.md'; t = idx.read_text(encoding='utf-8')
def cnt(rel):
    s = (root/'wiki'/rel).read_text(encoding='utf-8').split('---')[1]
    return sum(len(x.split(',')) for x in re.findall(r'^\s+- \S+: \[([^\]]*)\]', s, re.M))
t2 = re.sub(r'(\]\(([^)]+\.md)\) — .*?（引用 )\d+( 條）)', lambda m: f'{m[1]}{cnt(m[2])}{m[3]}', t)
idx.write_text(t2, encoding='utf-8', newline='\n'); print('changed' if t2 != t else 'same')
