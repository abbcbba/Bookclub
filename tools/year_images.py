"""연도별 읽은 책 목록 이미지(폰 세로 1080x1920)를 lists/ 에 만든다.

새 책을 books.js에 넣은 뒤 다시 실행해서 그해 이미지를 갱신한다.
필요한 것: python3, playwright(chromium), 글꼴 파일(아래 FONT_DIR)
  - gowun-batang-korean-700-normal.woff2, gowun-batang-latin-700-normal.woff2 (@fontsource/gowun-batang)
  - PretendardVariable.woff2 (npm pretendard)
실행: FONT_DIR=/글꼴/폴더 python3 tools/year_images.py
"""
import json, os, pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT_DIR = pathlib.Path(os.environ.get('FONT_DIR', ROOT / 'tools' / 'fonts')).resolve()
OUT = ROOT / 'lists'
MERGE = {2021: 2022}  # index.html과 같은 묶음 규칙
LC = {'영어': '#3F6E9E', '독일어': '#86A6C8', '한국어': '#2F6B57', '일본어': '#8DB596',
      '프랑스어': '#C8693E', '스페인어': '#E2A65B', '러시아어': '#8C6BAA'}

src = (ROOT / 'books.js').read_text(encoding='utf-8')
D = [json.loads(l.rstrip(',')) for l in src.split('\n') if l.startswith('[20')]
D.sort(key=lambda d: (d[0], d[1]))
groups = {}
for d in D:
    groups.setdefault(MERGE.get(d[0], d[0]), []).append(d)

def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def page(key, rows):
    years = sorted({d[0] for d in rows})
    multi = len(years) > 1
    label = f'{years[0]}–{str(years[-1])[2:]}' if multi else str(key)
    n = len(rows)
    rh = min(62, 1340 // n)
    fs = min(30, round(rh * 0.5))
    body = ''.join(
        f'<div class=r><span class=d>{(str(d[0])[2:] + ".") if multi else ""}{d[1]}</span>'
        f'<i style="background:{LC.get(d[5], "#ABA59C")}"></i><span class=t>{esc(d[2])}</span>'
        f'<span class=a>{esc(d[3])}</span></div>' for d in rows)
    f = FONT_DIR.as_uri()
    return label, f'''<!doctype html><meta charset=utf-8><style>
@font-face{{font-family:GB;font-weight:700;src:url({f}/gowun-batang-korean-700-normal.woff2)}}
@font-face{{font-family:GB;font-weight:700;src:url({f}/gowun-batang-latin-700-normal.woff2);unicode-range:U+0000-00FF,U+2013}}
@font-face{{font-family:PR;font-weight:45 920;src:url({f}/PretendardVariable.woff2) format('woff2-variations')}}
*{{margin:0;box-sizing:border-box}}
body{{width:1080px;height:1920px;background:#FFFFFF;color:#1F2226;font-family:PR;padding:120px 90px 0}}
.k{{font-size:30px;color:#6C6A63;font-weight:500}}
.y{{font-family:GB;font-weight:700;font-size:120px;line-height:1.05;margin-top:10px}}
.s{{font-size:34px;color:#A03A34;font-weight:600;margin:14px 0 50px}}
.r{{display:grid;grid-template-columns:{150 if multi else 110}px 18px 1fr auto;gap:22px;align-items:center;height:{rh}px;border-top:1px solid #EEEBE5;font-size:{fs}px}}
.d{{color:#6C6A63;font-variant-numeric:tabular-nums}}
.r i{{width:12px;height:{round(rh * 0.55)}px;border-radius:2px}}
.t{{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.a{{color:#6C6A63;font-size:.85em;white-space:nowrap}}
</style><div class=k>금요일 독서모임 기록</div><div class=y>{label}</div><div class=s>{n}권</div>{body}'''

OUT.mkdir(exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1080, 'height': 1920})
    tmp = OUT / '_tmp.html'
    for key, rows in sorted(groups.items()):
        label, html = page(key, rows)
        tmp.write_text(html, encoding='utf-8')
        pg.goto(tmp.as_uri()); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT / f"{label.replace('–', '-')}.png"))
        print(label, len(rows))
    tmp.unlink()
    b.close()
