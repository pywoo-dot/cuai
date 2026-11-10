from pathlib import Path
import numpy as np, pandas as pd, json, time
from collections import Counter
root=Path(r"C:\Users\박영우\Documents\심부름\2026-10_반도체박막AI연구\작업파일")
raw=root/"원본데이터"
result={}
train_sample=[]; labels=[]; hashes=[]
rng=np.random.default_rng(20261024)
chosen=np.sort(rng.choice(810000,20000,replace=False))
for name in ["train.csv","test.csv","sample_submission.csv"]:
    n=0; mins=None;maxs=None; sums=None;ss=None; missing=None;inf=None;neg=None;above=None; negrows=0
    adjacent=None; freqs={}; first=[]; last=[]
    for df in pd.read_csv(raw/name,chunksize=50000):
        a=df.to_numpy(dtype=np.float64); cols=list(df.columns)
        if mins is None:
            width=a.shape[1]; mins=np.full(width,np.inf);maxs=np.full(width,-np.inf)
            sums=np.zeros(width);ss=np.zeros(width);missing=np.zeros(width,dtype=np.int64);inf=missing.copy();neg=missing.copy();above=missing.copy()
            first=df.head(3).to_dict("records")
        finite=np.isfinite(a);clean=np.where(finite,a,0.)
        mins=np.minimum(mins,np.min(np.where(finite,a,np.inf),axis=0))
        maxs=np.maximum(maxs,np.max(np.where(finite,a,-np.inf),axis=0))
        sums+=clean.sum(axis=0);ss+=(clean**2).sum(axis=0)
        missing+=np.isnan(a).sum(axis=0);inf+=np.isinf(a).sum(axis=0)
        neg+=(a<0).sum(axis=0);above+=(a>1).sum(axis=0)
        spectral=[c for c in cols if c.isdigit()]
        if spectral:
            x=df[spectral].to_numpy()
            negrows+=int((x<0).any(axis=1).sum())
            cross=(x[:,:-1]*x[:,1:]).sum(axis=0)
            adjacent=cross if adjacent is None else adjacent+cross
        if name=="train.csv":
            y=df.iloc[:,:4].to_numpy()
            labels.append(y)
            for c in cols[:4]:
                freqs.setdefault(c,Counter()).update(df[c].value_counts().to_dict())
            keep=chosen[(chosen>=n)&(chosen<n+len(df))]-n
            train_sample.append(x[keep])
            hashes.append(pd.util.hash_pandas_object(df[spectral],index=False).to_numpy())
        n+=len(df);last=df.tail(3).to_dict("records")
        print(name,n,flush=True)
    stats={c:{"min":float(mins[i]),"max":float(maxs[i]),"mean":float(sums[i]/n),"std":float(np.sqrt(max(0,ss[i]/n-(sums[i]/n)**2))),"missing":int(missing[i]),"inf":int(inf[i]),"negative":int(neg[i]),"above_one":int(above[i])} for i,c in enumerate(cols)}
    item={"rows":n,"cols":len(cols),"stats":stats,"negative_spectrum_rows":negrows,"first_rows":first,"last_rows":last}
    if spectral:
        ix=[cols.index(c) for c in spectral]
        m=sums[ix]/n;s=ss[ix]/n-m*m
        cor=(adjacent/n-m[:-1]*m[1:])/np.sqrt(s[:-1]*s[1:])
        item["adjacent_channel_correlation"]={"min":float(cor.min()),"median":float(np.median(cor)),"max":float(cor.max())}
        item["spectrum_min"]=float(mins[ix].min());item["spectrum_max"]=float(maxs[ix].max())
        item["negative_spectrum_values"]=int(neg[ix].sum())
        item["above_one_spectrum_values"]=int(above[ix].sum())
    if name=="train.csv":
        y=np.concatenate(labels)
        combinations=np.unique(y,axis=0).shape[0]
        expected=np.array(np.unravel_index(np.arange(n),(30,30,30,30))).T*10+10
        item["target_combinations"]=combinations
        item["lexicographic_grid_exact"]=bool(np.array_equal(y,expected))
        item["target_frequencies"]={c:{str(k):int(v) for k,v in sorted(count.items())} for c,count in freqs.items()}
        h=np.concatenate(hashes);item["duplicate_spectrum_hashes"]=int(n-np.unique(h).size)
        x=np.concatenate(train_sample)
        centered=x-x.mean(axis=0);cov=centered.T@centered/(len(x)-1)
        vals=np.linalg.eigvalsh(cov)[::-1];cum=np.cumsum(vals)/vals.sum()
        item["sample_pca"]={"sample_size":len(x),"seed":20261024,"components_for_variance":{str(v):int(np.searchsorted(cum,v)+1) for v in [.90,.95,.99,.999]},"first_10_explained_ratios":(vals[:10]/vals.sum()).tolist()}
    result[name]=item
out=root/"原本実測プロファイル.json"
out=root/"원본_전수분석.json"
if out.exists(): raise RuntimeError("output exists")
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
print("SAVED",out,flush=True)
