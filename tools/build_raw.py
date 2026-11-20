"""從 data/documents.json 產生 raw/ 的 6 部法規原文（含回首頁導覽列）。
用法：python -X utf8 tools/build_raw.py .
會逐條比對，確認條文本文和 documents.json 一字不差。"""
import json, re, sys, pathlib
root = pathlib.Path(sys.argv[1])
d = json.loads((root/'data/documents.json').read_text(encoding='utf-8'))
six = ['職業安全衛生法','職業安全衛生設施規則','缺氧症預防規則','危害性化學品標示及通識規則','有機溶劑中毒預防規則','特定化學物質危害預防標準']
def key(no):
    m = re.fullmatch(r'第 (\d+)(?:-(\d+))? 條', no); return (int(m[1]), int(m[2] or 0))
out = root/'raw'; out.mkdir(exist_ok=True)
for law in six:
    arts = sorted([x for x in d if x['metadata']['law_name']==law], key=lambda x: key(x['metadata']['article_no']))
    m0 = arts[0]['metadata']
    pcode = re.search(r'pcode=(\w+)', m0['source_url'])[1]
    dates = {x['metadata']['amended_date'] for x in arts}; assert len(dates)==1
    lines = ['[🏠 首頁](../wiki/index.md) › 法規原文', '', f'# {law}', '',
             f'- 來源：全國法規資料庫 https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode={pcode}',
             f'- 修正日期：{m0["amended_date"]}',
             f'- 條數：{len(arts)} 條', '']
    for x in arts:
        head, body = x['text'].split('\n\n', 1)
        assert head == x['metadata']['title']
        lines += ['---', '', f'## {head.removeprefix(law+" ")}', '', body, '']
    lines += ['---', '', '[🏠 回首頁](../wiki/index.md)', '']
    (out/f'{law}.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    # verify verbatim
    txt = (out/f'{law}.md').read_text(encoding='utf-8')
    assert all(x['text'].split('\n\n',1)[1] in txt for x in arts)
    print(law, len(arts))
