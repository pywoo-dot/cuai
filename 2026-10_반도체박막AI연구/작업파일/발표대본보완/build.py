from pathlib import Path
import re, html
import pymupdf
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

root=Path('C:/Users/박영우/Documents/심부름/2026-10_반도체박막AI연구')
build=root/'작업파일/발표대본보완'
source=pymupdf.open('C:/Users/박영우/iCloudDrive/CUAI/cuai_1027발표대본.pdf')
# Preserve original wording and distinguish visual line wraps from paragraph ends.
pages=[]
for page in source:
    lines=page.get_text().splitlines()
    paras=[]; current=''
    for line in lines:
        t=line.strip()
        if not t:
            if current: paras.append(current); current=''
            continue
        if re.match(r'P\.\d',t):
            if current: paras.append(current); current=''
            paras.append(t); continue
        # The original PDF wraps Korean words; repair those exact wrapped forms below.
        current += (' ' if current else '')+t
        if t.endswith(('.', '?')):
            paras.append(current); current=''
    if current: paras.append(current)
    pages.extend(paras)
text='\n\n'.join(pages)
for a,b in [('보고 자','보고자'),('있을 까','있을까'),('프로 젝트','프로젝트'),('예 측','예측'),('통 해','통해'),('그치 지','그치지'),('입 니다','입니다'),('것입 니다','것입니다'),('오차 가','오차가'),('변 화','변화'),('앞으 로','앞으로'),('예측합 니다','예측합니다'),('동 일한','동일한'),('것입니 다','것입니다'),('영향을 미치는지','영향을 미치는지'),('안정적 으로','안정적으로'),('때문 에','때문에'),('층에 서','층에서'),('추 가되어도','추가되어도'),('불 안정','불안정')]:
    text=text.replace(a,b)
changes={
 '먼저 프로젝트에 사용할 데이터입니다.':'먼저 프로젝트에 사용할 데이터입니다.\n\n데이터는 데이콘의 ‘반도체 박막 두께 분석 경진대회’에서 제공한 자료를 사용할 예정입니다.',
 '잡음이 없는 원본 데이터':'추가 잡음을 넣기 전의 원본 데이터',
 '잡음이 없는 데이터와 잡음이 추가된 데이터':'원본 데이터와 추가 잡음을 넣은 데이터',
 '잡음의 유무를 제외한':'추가 잡음 조건을 제외한',
 '추가하기 전후로 예측값 자체가 얼마나 달라지는지를 확인할 것입니다.':'추가하기 전후로 예측값 자체가 얼마나 달라지는지를 확인할 것입니다.\n\n정답 대비 예측 오차는 절대오차를 보는 MAE와 상대오차를 보는 MAPE로 함께 비교할 계획입니다. 같은 크기의 오차라도 박막 두께에 따라 차지하는 비율이 달라지기 때문입니다.'
}
for old,new in changes.items():
    assert old in text, old
    text=text.replace(old,new,1)
(build/'수정본문.txt').write_text(text,encoding='utf-8')
pdfmetrics.registerFont(TTFont('Malgun','C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunBold','C:/Windows/Fonts/malgunbd.ttf'))
body=ParagraphStyle('Body',fontName='Malgun',fontSize=11,leading=19,spaceAfter=4,wordWrap='CJK')
head=ParagraphStyle('Head',parent=body,fontName='MalgunBold',spaceBefore=12,spaceAfter=9,keepWithNext=True)
story=[]
for p in text.split('\n\n'):
    if p.strip()=='.': continue
    ishead=bool(re.match(r'P\.\d',p))
    if False: story.append(PageBreak())
    story.append(Paragraph(html.escape(p),head if ishead else body))
out=root/'최종/cuai_1027발표대본_출처와평가지표추가.pdf'
out=build/'검수완료.pdf'
SimpleDocTemplate(str(out),pagesize=(595.32,841.92),leftMargin=72,rightMargin=72,topMargin=63,bottomMargin=55,title='CUAI 주제발표 대본',author='').build(story)
doc=pymupdf.open(out)
for i,p in enumerate(doc): p.get_pixmap(matrix=pymupdf.Matrix(1.3,1.3)).save(str(build/f'page-{i+1}.png'))
print(str(out)); print('pages',len(doc)); print(text)

