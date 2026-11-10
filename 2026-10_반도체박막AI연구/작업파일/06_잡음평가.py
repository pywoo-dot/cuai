"""
06_잡음평가.py

학습이 끝난 MLP 3개(seed 0·1·2)에 잡음을 넣은 반사율을 주고,
두께 예측이 얼마나 나빠지고(정확도) 얼마나 흔들리는지(일관성) 측정한다.
새로 학습하지 않는다. 저장된 모델로 예측만 한다.

잡음 조건 (팀 공유 기획안)
  S0: σ = 0       추가 잡음 없음 (기준)
  S1: σ = 0.0025
  S2: σ = 0.005
  S3: σ = 0.01
  S4: σ = 0.02    각 10회 반복 (잡음 난수 100~109)

  x_잡음 = x_원본 + σ × z,   z ~ 평균 0·표준편차 1의 정규분포
  - 잡음은 표준화 전 '원래 반사율 값'에 더한다.
  - 같은 반복 번호에서는 같은 z를 쓰고 σ만 바꾼다. 세 모델에도 똑같은 잡음을 준다.

실행:  python 06_잡음평가.py          → 검증(val) 분할로 예비 평가
       python 06_잡음평가.py test     → 최종평가 분할 (설정을 팀이 확정한 뒤에만!)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch import nn

SPLIT = sys.argv[1] if len(sys.argv) > 1 else "val"
# 평가할 모델 파일 이름표: "_yscaled" = 100 epoch판, "_yscaled_lrs" = 300 epoch + 학습률 스케줄러판
MODEL_TAG = sys.argv[2] if len(sys.argv) > 2 else "_yscaled_lrs"
TRAIN_SEEDS = [0, 1, 2]
NOISE_LEVELS = {"S0": 0.0, "S1": 0.0025, "S2": 0.005, "S3": 0.01, "S4": 0.02}
NOISE_SEEDS = list(range(100, 110))

# 두께 구간: 해당 층의 정답 두께로 분류
BINS = {"얇음(10~100)": (10, 100), "중간(110~200)": (110, 200), "두꺼움(210~300)": (210, 300)}
LAYERS = ["layer_1", "layer_2", "layer_3", "layer_4"]

work_dir = Path(__file__).parent
result_dir = work_dir / "결과"

# ----------------------------------------------------------------------
# 1. 평가 데이터 불러오기 (원래 반사율 값 그대로)
# ----------------------------------------------------------------------
X_all = np.load(work_dir / "캐시" / "X_all.npy")
y_all = np.load(work_dir / "캐시" / "y_all.npy")
idx = np.load(work_dir / "공통분할" / "split_indices.npz")[f"{SPLIT}_idx"]
scaler = np.load(work_dir / "공통분할" / "input_scaler_train_only.npz")
x_mean = scaler["mean"].astype(np.float32)
x_std = scaler["std"].astype(np.float32)

X_raw = X_all[idx]          # (표본 수, 226)
y_true = y_all[idx]         # (표본 수, 4)
del X_all, y_all
print(f"평가 분할: {SPLIT}  모델: {MODEL_TAG}  표본 수: {len(X_raw):,}")


# ----------------------------------------------------------------------
# 2. 저장된 모델 불러오기
# ----------------------------------------------------------------------
def load_model(seed):
    ckpt = torch.load(result_dir / f"mlp_seed{seed}{MODEL_TAG}_best.pt")
    hidden = ckpt.get("hidden", 160)      # 저장할 때 적어 둔 뉴런 수 (없으면 기준 모델의 160)
    model = nn.Sequential(
        nn.Linear(226, hidden), nn.ReLU(),
        nn.Linear(hidden, hidden), nn.ReLU(),
        nn.Linear(hidden, hidden), nn.ReLU(),
        nn.Linear(hidden, 4),
    )
    model.load_state_dict(ckpt["model"])
    model.eval()
    return model, ckpt["y_mean"], ckpt["y_std"]


def predict(model, y_mean, y_std, X):
    """원래 반사율 X → (표준화) → 모델 → 원래 두께 단위 예측"""
    X_scaled = torch.from_numpy((X - x_mean) / x_std)
    outs = []
    with torch.no_grad():
        for start in range(0, len(X_scaled), 16384):
            outs.append(model(X_scaled[start:start + 16384]) * y_std + y_mean)
    return torch.cat(outs).numpy()


# ----------------------------------------------------------------------
# 3. 지표 계산
#   MAE  : |예측 - 정답|의 평균
#   MAPE : |예측 - 정답| / 정답 의 평균 × 100 (%)
#   D    : |잡음 예측 - 원본 예측|의 평균 (정답과 무관한 '흔들림')
#   P95  : 표본마다 4층 절대오차를 평균한 값의 95백분위 (큰 실패)
# ----------------------------------------------------------------------
def compute_rows(pred, pred0, base):
    abs_err = np.abs(pred - y_true)                 # (N, 4)
    rel_err = abs_err / y_true * 100
    change = np.abs(pred - pred0)
    rows = []
    rows.append({**base, "층": "전체", "구간": "전체", "표본수": len(pred),
                 "MAE": abs_err.mean(), "MAPE": rel_err.mean(), "D": change.mean(),
                 "P95": np.percentile(abs_err.mean(axis=1), 95)})
    for k, layer in enumerate(LAYERS):
        rows.append({**base, "층": layer, "구간": "전체", "표본수": len(pred),
                     "MAE": abs_err[:, k].mean(), "MAPE": rel_err[:, k].mean(),
                     "D": change[:, k].mean(), "P95": np.nan})
        for bin_name, (lo, hi) in BINS.items():
            m = (y_true[:, k] >= lo) & (y_true[:, k] <= hi)
            rows.append({**base, "층": layer, "구간": bin_name, "표본수": int(m.sum()),
                         "MAE": abs_err[m, k].mean(), "MAPE": rel_err[m, k].mean(),
                         "D": change[m, k].mean(), "P95": np.nan})
    return rows


# ----------------------------------------------------------------------
# 4. 평가 반복: 모델 3개 × (S0 1회 + S1~S4 각 10회) = 123회 예측
# ----------------------------------------------------------------------
models = {s: load_model(s) for s in TRAIN_SEEDS}
pred0 = {s: predict(*models[s], X_raw) for s in TRAIN_SEEDS}    # S0 예측 저장

rows = []
for s in TRAIN_SEEDS:
    rows += compute_rows(pred0[s], pred0[s], {"학습seed": s, "조건": "S0", "sigma": 0.0, "잡음반복": -1})

for rep, noise_seed in enumerate(NOISE_SEEDS):
    z = np.random.default_rng(noise_seed).standard_normal(X_raw.shape).astype(np.float32)
    for cond, sigma in NOISE_LEVELS.items():
        if sigma == 0:
            continue
        X_noisy = X_raw + sigma * z        # 원본은 그대로 두고 매번 새로 더함
        for s in TRAIN_SEEDS:
            pred = predict(*models[s], X_noisy)
            rows += compute_rows(pred, pred0[s], {"학습seed": s, "조건": cond, "sigma": sigma, "잡음반복": rep})
    print(f"잡음 반복 {rep + 1}/{len(NOISE_SEEDS)} 완료")

df = pd.DataFrame(rows)
out_path = result_dir / f"잡음평가_{SPLIT}{MODEL_TAG}_전체기록.csv"
df.to_csv(out_path, index=False, encoding="utf-8-sig")

# ----------------------------------------------------------------------
# 5. 요약: 잡음 반복 10회 평균 → 학습 seed 3개의 평균 ± 표준편차
# ----------------------------------------------------------------------
per_seed = df.groupby(["조건", "sigma", "층", "구간", "학습seed"], as_index=False)[
    ["MAE", "MAPE", "D", "P95"]].mean()
s0 = per_seed[per_seed["조건"] == "S0"][["층", "구간", "학습seed", "MAE", "MAPE"]]
per_seed = per_seed.merge(s0, on=["층", "구간", "학습seed"], suffixes=("", "_S0"))
per_seed["ΔMAE"] = per_seed["MAE"] - per_seed["MAE_S0"]
per_seed["ΔMAPE"] = per_seed["MAPE"] - per_seed["MAPE_S0"]


def mean_std(frame, keys, cols):
    g = frame.groupby(keys)[cols]
    m, sd = g.mean(), g.std(ddof=1)
    return m.round(3).astype(str) + " ± " + sd.round(3).astype(str)


pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 20)

overall = per_seed[(per_seed["층"] == "전체") & (per_seed["구간"] == "전체")]
print("\n[1] 전체: 잡음 세기별 (학습 seed 3개 평균 ± 표준편차)")
print(mean_std(overall, ["조건", "sigma"], ["MAE", "ΔMAE", "MAPE", "ΔMAPE", "D", "P95"]))

layer = per_seed[(per_seed["층"] != "전체") & (per_seed["구간"] == "전체")]
print("\n[2] 층별 MAE")
print(layer.pivot_table(index="조건", columns="층", values="MAE", aggfunc="mean").round(2))
print("\n[3] 층별 ΔMAE (S0 대비 증가량)")
print(layer.pivot_table(index="조건", columns="층", values="ΔMAE", aggfunc="mean").round(2))
print("\n[4] 층별 예측 변화량 D")
print(layer.pivot_table(index="조건", columns="층", values="D", aggfunc="mean").round(2))

bins = per_seed[(per_seed["층"] != "전체") & (per_seed["구간"] != "전체") & per_seed["조건"].isin(["S0", "S3"])]
print("\n[5] 두께 구간별 MAE / MAPE(%) — S0와 S3")
print(bins.pivot_table(index=["층", "구간"], columns="조건", values=["MAE", "MAPE", "ΔMAE"], aggfunc="mean").round(2))

summary_path = result_dir / f"잡음평가_{SPLIT}{MODEL_TAG}_seed별요약.csv"
per_seed.to_csv(summary_path, index=False, encoding="utf-8-sig")
print("\n저장:", out_path.name, ",", summary_path.name)
