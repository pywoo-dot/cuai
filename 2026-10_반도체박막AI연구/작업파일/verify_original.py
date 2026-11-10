from pathlib import Path
import csv, json, shutil, datetime
base=Path(r"C:\Users\박영우\Documents\심부름")
task=base/"2026-10_반도체박막AI연구"
raw=task/"작업파일"/"원본데이터"
manifest={}
for name in ["train.csv","test.csv","sample_submission.csv"]:
    p=raw/name
    with p.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.reader(f); header=next(reader); first=next(reader)
    lines=0; last=b""
    with p.open("rb") as f:
        while True:
            block=f.read(8*1024*1024)
            if not block: break
            lines+=block.count(b"\n"); last=block[-1:]
    rows=lines-1+(1 if last!=b"\n" else 0)
    manifest[name]={"rows":rows,"columns":len(header),"bytes":p.stat().st_size,"header":header,"first_row_width":len(first)}
    print(name,rows,len(header),p.stat().st_size,flush=True)
assert manifest["train.csv"]["columns"]==230
assert manifest["test.csv"]["columns"]==227
assert manifest["sample_submission.csv"]["columns"]==5
(task/"작업파일"/"원본파일_명세.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf-8")
note="""# 반도체 박막 원본 데이터 확보

> 2026-10-24 공식 다운로드 링크에서 ZIP과 CSV 3개를 확보하고 읽기를 확인했다.

[대회 데이터 페이지](https://dacon.io/competitions/official/235554/data)의 다운로드 버튼은 아래 Google Drive 파일을 새 탭으로 연다.
[공식 원본 ZIP 다운로드](https://drive.google.com/file/d/1ddYwIEmXFllS7CGh3l-cmRf3o1gNaMNV/view)

Google Drive 화면에는 링크가 있는 누구나 접근 가능하며 로그인이 필요 없다고 표시됐다.
실제로 별도 인증정보 없이 공개 파일을 내려받았다.
ZIP은 831,341,219 bytes이며 압축 해제 중 CRC 검증 오류 없이 세 CSV의 끝까지 읽었다.

| 파일 | 데이터 행 수 | 열 수 | 원본 크기(bytes) |
|---|---:|---:|---:|
"""
for name,m in manifest.items():
    note+=f"| {name} | {m['rows']:,} | {m['columns']} | {m['bytes']:,} |\n"
note+="""
## 저장 위치

원본 ZIP과 CSV는 작업파일/원본데이터/에 보관했다. 원본은 수정하지 않았다.
행 수는 파일 전체 줄바꿈을 세어 헤더를 제외했고, 열 수와 첫 행은 CSV 파서로 확인했다.
결측·중복·분포의 전수 분석은 이번 확인에 포함하지 않았다.

## 이전 안내 정정

이전에는 계정의 다운로드 화면에서 참가·인증 안내가 나온 것을 근거로 원본 접근이 어렵다고 안내했다.
이후 재확인 시 대회 페이지가 참여중으로 표시됐고, 다운로드 버튼이 공개 Google Drive 파일을 여는 것을 확인했다.
참가 등록이나 휴대폰 인증을 대신 진행하지 않았다.
원본 확보는 이제 완료됐으므로 대체 합성 데이터는 필수 조건이 아니다.

## 다음 작업

확보한 CSV로 결측·무한값·중복·두께 조합·반사율 범위·채널 상관·학습/시험 분포를 확인할 수 있다.
회의자료 전체 구성은 앞서 작성한 구성 샘플을 기준으로 사용자 확인 대기 상태다.
"""
(task/"최종"/"반도체박막_원본데이터_확보안내.md").write_text(note,encoding="utf-8")
stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
bk=task/"작업파일"/("상태백업_"+stamp);bk.mkdir()
readme=task/"README.md";shutil.copy2(readme,bk/"README.md")
text=readme.read_text(encoding="utf-8")
text=text.replace("현재 구성 샘플 확인 및 원본 확보 대기.","원본 CSV 확보 완료. 상세 회의자료 구성 확인 대기.")
text=text.replace("- 상태: 진행 중","- 상태: 진행 중 · 원본 데이터 확보 완료")
text+="\n## 원본 확보 업데이트 — 2026-10-24\n\n공식 공개 ZIP 다운로드·CSV 3개 압축 해제·헤더 및 전체 행 수 확인 완료.\n[원본 확보 안내](최종/반도체박막_원본데이터_확보안내.md)를 우선 확인한다.\n이전 본문의 원본 미확보·로그인 대기 내용은 이 업데이트로 대체한다.\n"
readme.write_text(text,encoding="utf-8")
root=base/"README.md";shutil.copy2(root,bk/"심부름_README.md")
text=root.read_text(encoding="utf-8").replace("진행 중 · 구성 샘플·공개 자료 조사 / 로그인 대기","진행 중 · 원본 CSV 3개 확보·명세 검증 / 구성 샘플 확인 대기")
root.write_text(text,encoding="utf-8")
