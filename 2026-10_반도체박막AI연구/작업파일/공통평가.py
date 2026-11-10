"""
공통평가.py — 팀원 모델을 같은 조건으로 잡음 평가하기 위한 공통 도구

어떤 모델이든 '원래 반사율(226개) → 원래 단위 두께(4개)'로 예측하는 함수만 있으면
06_잡음평가.py(MLP)와 똑같은 데이터·잡음·지표로 평가할 수 있다.

사용 예)
    from 공통평가 import evaluate

    def my_predict(X_raw):          # X_raw: (N, 226) 원래 반사율, float32 numpy 배열
        ...                          # 표준화 등 전처리는 모델 쪽에서 직접 한다
        return pred                  # (N, 4) 원래 두께 단위 numpy 배열

    evaluate(my_predict, model_name="홍길동_RandomForest", split="val")

규칙 (06_잡음평가.py와 동일)
  - 평가 행: 공통분할/split_indices.npz 의 {split}_idx 순서 그대로
  - 잡음: x_잡음 = x_원본 + σ × z,  z = np.random.default_rng(잡음seed).standard_normal((N, 226))
           σ = 0 / 0.0025 / 0.005 / 0.01 / 0.02 (S0~S4), 잡음seed 100~109
  - 지표: MAE, MAPE(%), ΔMAE, ΔMAPE, D(예측 변화량), P95, 층별, 두께 구간별
  - 원본 데이터는 train.csv 하나만 쓴다 (test.csv 에는 정답이 없다)

최종평가(test) 분할은 팀이 모델·지표를 확정하기 전에는 쓰지 않는다.
"""

from pathlib import Path

import numpy as np
import pandas as pd

NOISE_LEVELS = {"S0": 0.0, "S1": 0.0025, "S2": 0.005, "S3": 0.01, "S4": 0.02}
NOISE_SEEDS = list(range(100, 110))
BINS = {"얇음(10~100)": (10, 100), "중간(110~200)": (110, 200), "두꺼움(210~300)": (210, 300)}
LAYERS = ["layer_1", "layer_2", "layer_3", "layer_4"]

work_dir = Path(__file__).parent


def load_split(split="val"):
    """공통 분할의 원래 반사율 X (N, 226)와 정답 두께 y (N, 4)를 돌려준다.
    캐시(04_공통분할_만들기.py가 만든 npy)가 있으면 그것을, 없으면 train.csv를 읽는다."""
    idx = np.load(work_dir / "공통분할" / "split_indices.npz")[f"{split}_idx"]
    cache = work_dir / "캐시"
    if (cache / "X_all.npy").exists():
        X_all = np.load(cache / "X_all.npy", mmap_mode="r")
        y_all = np.load(cache / "y_all.npy", mmap_mode="r")
        return np.asarray(X_all[idx], dtype=np.float32), np.asarray(y_all[idx], dtype=np.float32)
    df = pd.read_csv(work_dir / "원본데이터" / "train.csv", dtype=np.float32)
    y = df[LAYERS].to_numpy()[idx]
    X = df[[str(i) for i in range(226)]].to_numpy()[idx]
    return X, y


def noisy_inputs(X_raw):
    """(조건, σ, 반복번호, 잡음 입력)을 차례로 내놓는다. S0은 1번, S1~S4는 10번씩."""
    yield "S0", 0.0, -1, X_raw
    for rep, seed in enumerate(NOISE_SEEDS):
        z = np.random.default_rng(seed).standard_normal(X_raw.shape).astype(np.float32)
        for cond, sigma in NOISE_LEVELS.items():
            if sigma > 0:
                yield cond, sigma, rep, X_raw + sigma * z


def metric_rows(pred, pred0, y_true, base):
    """한 번의 예측에 대한 지표 행 목록 (전체 1행 + 층별 4행 + 층×구간 12행)."""
    abs_err = np.abs(pred - y_true)
    rel_err = abs_err / y_true * 100
    change = np.abs(pred - pred0)
    rows = [{**base, "층": "전체", "구간": "전체", "표본수": len(pred),
             "MAE": abs_err.mean(), "MAPE": rel_err.mean(), "D": change.mean(),
             "P95": np.percentile(abs_err.mean(axis=1), 95)}]
    for k, layer in enumerate(LAYERS):
        rows.append({**base, "층": layer, "구간": "전체", "표본수": len(pred),
                     "MAE": abs_err[:, k].mean(), "MAPE": rel_err[:, k].mean(),
                     "D": change[:, k].mean(), "P95": np.nan})
        for name, (lo, hi) in BINS.items():
            m = (y_true[:, k] >= lo) & (y_true[:, k] <= hi)
            rows.append({**base, "층": layer, "구간": name, "표본수": int(m.sum()),
                         "MAE": abs_err[m, k].mean(), "MAPE": rel_err[m, k].mean(),
                         "D": change[m, k].mean(), "P95": np.nan})
    return rows


def evaluate(predict_fn, model_name, split="val", train_seed=0, data=None, save=True):
    """predict_fn 하나(학습 seed 하나)를 S0~S4로 평가해 지표 표(DataFrame)를 돌려준다.
    학습 seed를 여러 개 쓰면 seed마다 부르고 결과를 합친다."""
    X_raw, y_true = data if data is not None else load_split(split)
    pred0, rows = None, []
    for cond, sigma, rep, X in noisy_inputs(X_raw):
        pred = np.asarray(predict_fn(X), dtype=np.float64)
        if pred0 is None:
            pred0 = pred
        rows += metric_rows(pred, pred0, y_true,
                            {"모델": model_name, "학습seed": train_seed, "조건": cond, "sigma": sigma, "잡음반복": rep})
    df = pd.DataFrame(rows)
    if save:
        out = work_dir / "결과" / f"공통평가_{split}_{model_name}_seed{train_seed}.csv"
        df.to_csv(out, index=False, encoding="utf-8-sig")
        print("저장:", out.name)
    overall = df[(df["층"] == "전체") & (df["구간"] == "전체")]
    print(overall.groupby(["조건", "sigma"])[["MAE", "MAPE", "D", "P95"]].mean().round(3))
    return df
