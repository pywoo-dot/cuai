"""
04_공통분할_만들기.py

목적
1) train.csv 전체 810,000행을 한 번만 읽어서, 빠르게 다시 불러올 수 있는 .npy 파일로 저장한다.
2) 전체 행 번호를 한 번만 섞어서 학습 80% / 검증 10% / 최종평가 10%로 나눈다.
   -> 팀원 모두 이 행 번호 파일을 쓰면 '같은 데이터'로 모델을 비교할 수 있다.
3) 입력 표준화에 쓸 평균·표준편차를 '학습 분할'에서만 계산해 저장한다.

이 스크립트는 한 번만 실행하면 된다. 다음 단계(05_모델학습.py)는 여기서 만든 파일을 읽는다.
"""

from pathlib import Path

import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# 0. 경로와 고정값
# ----------------------------------------------------------------------
work_dir = Path(__file__).parent
csv_path = work_dir / "원본데이터" / "train.csv"

share_dir = work_dir / "공통분할"   # 팀원과 공유할 파일 (작음)
cache_dir = work_dir / "캐시"       # 내 컴퓨터에서만 쓰는 빠른 데이터 (큼, 공유 불필요)
share_dir.mkdir(exist_ok=True)
cache_dir.mkdir(exist_ok=True)

SPLIT_SEED = 2026          # 기획안에서 제안한 분할 난수
N_TOTAL = 810_000
N_TRAIN = 648_000          # 80%
N_VAL = 81_000             # 10%
N_TEST = 81_000            # 10%  (최종 평가용: 모델 선택에 쓰지 않는다)

input_columns = [str(i) for i in range(226)]
target_columns = ["layer_1", "layer_2", "layer_3", "layer_4"]

# ----------------------------------------------------------------------
# 1. CSV 전체를 읽어서 NumPy 배열로 모으기
#    - 2GB 파일을 한 번에 읽으면 메모리를 많이 쓰므로 100,000행씩 나눠 읽는다.
#    - float32: 소수 하나를 4바이트로 저장 (기본 float64의 절반 메모리).
# ----------------------------------------------------------------------
X_all = np.empty((N_TOTAL, 226), dtype=np.float32)
y_all = np.empty((N_TOTAL, 4), dtype=np.float32)

row = 0
for part in pd.read_csv(csv_path, chunksize=100_000):
    n = len(part)
    X_all[row:row + n] = part[input_columns].to_numpy(dtype=np.float32)
    y_all[row:row + n] = part[target_columns].to_numpy(dtype=np.float32)
    row += n
    print(f"CSV 읽는 중... {row:,} / {N_TOTAL:,} 행")

assert row == N_TOTAL, f"행 수가 예상과 다릅니다: {row}"

np.save(cache_dir / "X_all.npy", X_all)
np.save(cache_dir / "y_all.npy", y_all)
print("\n캐시 저장 완료:", cache_dir)

# ----------------------------------------------------------------------
# 2. 전체 행 번호를 한 번만 섞어서 나누기
#    - default_rng(seed): 같은 seed면 언제 실행해도 같은 난수가 나오는 생성기
#    - permutation(N): 0 ~ N-1 숫자를 무작위 순서로 섞은 배열
# ----------------------------------------------------------------------
rng = np.random.default_rng(SPLIT_SEED)
shuffled = rng.permutation(N_TOTAL)

train_idx = np.sort(shuffled[:N_TRAIN])
val_idx = np.sort(shuffled[N_TRAIN:N_TRAIN + N_VAL])
test_idx = np.sort(shuffled[N_TRAIN + N_VAL:])

# 겹치는 행이 없고, 합치면 전체가 되는지 확인
assert len(np.intersect1d(train_idx, val_idx)) == 0
assert len(np.intersect1d(train_idx, test_idx)) == 0
assert len(np.intersect1d(val_idx, test_idx)) == 0
assert len(train_idx) + len(val_idx) + len(test_idx) == N_TOTAL

# 팀원용 1: NumPy 파일
np.savez(share_dir / "split_indices.npz",
         train_idx=train_idx, val_idx=val_idx, test_idx=test_idx)

# 팀원용 2: CSV 파일 (train.csv의 각 행이 어느 분할인지)
split_label = np.empty(N_TOTAL, dtype=object)
split_label[train_idx] = "train"
split_label[val_idx] = "val"
split_label[test_idx] = "test"
pd.DataFrame({"row": np.arange(N_TOTAL), "split": split_label}).to_csv(
    share_dir / "split_labels.csv", index=False)

print("\n분할 결과")
print("학습:", len(train_idx), " 검증:", len(val_idx), " 최종평가:", len(test_idx))

# ----------------------------------------------------------------------
# 3. 표준화 통계: 학습 분할에서만 계산 (검증·평가 정보가 새지 않게)
# ----------------------------------------------------------------------
X_train = X_all[train_idx].astype(np.float64)
train_mean = X_train.mean(axis=0)
train_std = X_train.std(axis=0)
train_std[train_std == 0] = 1.0
np.savez(share_dir / "input_scaler_train_only.npz", mean=train_mean, std=train_std)
del X_train

# ----------------------------------------------------------------------
# 4. 확인: 각 분할에서 층별 두께 값(10~300, 30종류)이 고르게 들어갔는가
# ----------------------------------------------------------------------
print("\n각 분할에서 두께 값별 표본 수 (최소 ~ 최대)")
for name, idx in [("학습", train_idx), ("검증", val_idx), ("최종평가", test_idx)]:
    text = []
    for k, col in enumerate(target_columns):
        _, counts = np.unique(y_all[idx, k], return_counts=True)
        text.append(f"{col}: {counts.min()}~{counts.max()}")
    print(f"{name:5s} |", " | ".join(text))

print("\n팀원 확인용: 최종평가 행 번호 앞 5개 =", test_idx[:5].tolist())
print("저장한 공유 파일:", share_dir)
