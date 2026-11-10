from pathlib import Path
import requests, time, hashlib, zipfile, shutil
from bs4 import BeautifulSoup
root=Path(r"C:\Users\박영우\Documents\심부름\2026-10_반도체박막AI연구\작업파일")
out=root/"원본데이터"
out.mkdir(exist_ok=True)
dest=out/"235554_반도체박막_data.zip"
if dest.exists(): raise SystemExit("File already exists; not overwriting")
sess=requests.Session()
url="https://drive.usercontent.google.com/download"
params={"id":"1ddYwIEmXFllS7CGh3l-cmRf3o1gNaMNV","export":"download"}
r=sess.get(url,params=params,timeout=45)
r.raise_for_status()
if "text/html" in r.headers.get("Content-Type",""):
    soup=BeautifulSoup(r.text,"html.parser")
    form=soup.find("form")
    if not form: raise RuntimeError("Download form unavailable")
    params={i.get("name"):i.get("value","") for i in form.find_all("input") if i.get("name")}
    r=sess.get(form["action"],params=params,stream=True,timeout=(30,90))
else:
    r=sess.get(url,params=params,stream=True,timeout=(30,90))
r.raise_for_status()
if "text/html" in r.headers.get("Content-Type",""): raise RuntimeError("Received HTML instead of ZIP")
partial=dest.with_suffix(".zip.partial")
if partial.exists(): raise RuntimeError("Partial file already exists")
size=0; last=0; start=time.monotonic(); sha=hashlib.sha256()
with partial.open("xb") as f:
    for chunk in r.iter_content(1024*1024):
        if not chunk: continue
        f.write(chunk); sha.update(chunk); size+=len(chunk)
        if size-last>=25*1024*1024:
            print(f"Downloaded {size/1024**2:.0f} MiB; elapsed {time.monotonic()-start:.0f}s",flush=True);last=size
partial.rename(dest)
print(f"ZIP complete: {size} bytes; SHA256 {sha.hexdigest()}",flush=True)
with zipfile.ZipFile(dest) as z:
    print([(i.filename,i.file_size) for i in z.infolist()],flush=True)
    for i in z.infolist():
        name=Path(i.filename).name
        if name.lower() in {"train.csv","test.csv","sample_submission.csv"}:
            target=out/name
            if target.exists(): raise RuntimeError("CSV already exists")
            with z.open(i) as a,target.open("xb") as b: shutil.copyfileobj(a,b)
            print(f"Extracted {name}: {target.stat().st_size} bytes",flush=True)
(root/"원본다운로드_검증.txt").write_text(f"Source: https://drive.google.com/file/d/1ddYwIEmXFllS7CGh3l-cmRf3o1gNaMNV/view\nBytes: {size}\nSHA256: {sha.hexdigest()}\n",encoding="utf-8")
