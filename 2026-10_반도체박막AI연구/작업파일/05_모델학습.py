"""
05_모델학습.py

04에서 만든 공통 분할로 MLP를 실제로 학습한다.
  1) 캐시 데이터와 분할 불러오기 → 입력 표준화
  2) 기준 모델(학습 데이터 층별 중앙값)의 검증 MAE
  3) 미니배치 + epoch 반복 학습
  4) 매 epoch 검증 MAE 계산, 가장 좋은 가중치 저장, 조기 종료

최종평가(test) 분할은 여기서 전혀 사용하지 않는다.
"""

import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

# ----------------------------------------------------------------------
# 0. 설정값 (기획안의 시작 제안값)
# ----------------------------------------------------------------------
# 학습 난수 (기획안: 0, 1, 2). 실행할 때 뒤에 숫자를 붙이면 그 seed를 사용한다.
#   예) python 05_모델학습.py 1   → seed 1     (숫자 없이 실행하면 seed 0)
TRAIN_SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 0
# 은닉층 한 층의 뉴런 수. 두 번째 숫자로 바꿀 수 있다.
#   예) python 05_모델학습.py 0 512  → seed 0, 뉴런 512개   (안 쓰면 기준 모델의 160)
HIDDEN = int(sys.argv[2]) if len(sys.argv) > 2 else 160
BATCH_SIZE = 1024       # 한 번에 가중치를 고칠 때 쓰는 표본 수
LEARNING_RATE = 0.001
MAX_EPOCHS = 300        # 기록: 예비 5 → 1차 100 → 수렴 확인용 300
PATIENCE = 20           # 검증 MAE가 20 epoch 연속 좋아지지 않으면 멈춤
SCALE_TARGET = True     # True: 정답 두께도 표준화해서 학습 (평가는 항상 원래 두께 단위)
USE_LR_SCHEDULER = True # True: 검증 MAE가 정체되면 학습률을 절반으로 줄임
LR_PATIENCE = 5         #   5 epoch 동안 좋아지지 않으면 줄인다

work_dir = Path(__file__).parent
result_dir = work_dir / "결과"
result_dir.mkdir(exist_ok=True)
tag = ("_yscaled" if SCALE_TARGET else "") + ("_lrs" if USE_LR_SCHEDULER else "")
if HIDDEN != 160:
    tag += f"_h{HIDDEN}"
best_model_path = result_dir / f"mlp_seed{TRAIN_SEED}{tag}_best.pt"

torch.manual_seed(TRAIN_SEED)

# ----------------------------------------------------------------------
# 1. 데이터 불러오기
# ----------------------------------------------------------------------
X_all = np.load(work_dir / "캐시" / "X_all.npy")
y_all = np.load(work_dir / "캐시" / "y_all.npy")
split = np.load(work_dir / "공통분할" / "split_indices.npz")
scaler = np.load(work_dir / "공통분할" / "input_scaler_train_only.npz")

train_idx = split["train_idx"]
val_idx = split["val_idx"]

mean = scaler["mean"].astype(np.float32)
std = scaler["std"].astype(np.float32)

# 표준화: (값 - 학습 평균) / 학습 표준편차
X_train = torch.from_numpy((X_all[train_idx] - mean) / std)
y_train = torch.from_numpy(y_all[train_idx])
X_val = torch.from_numpy((X_all[val_idx] - mean) / std)
y_val = torch.from_numpy(y_all[val_idx])
del X_all, y_all   # 메모리 절약

print("학습:", tuple(X_train.shape), "검증:", tuple(X_val.shape))

# ----------------------------------------------------------------------
# 2. 기준 모델: 입력을 보지 않고 학습 데이터의 층별 중앙값만 출력
#    MLP가 이것보다 훨씬 좋아야 '입력에서 무언가를 배웠다'고 말할 수 있다.
# ----------------------------------------------------------------------
median = y_train.median(dim=0).values                  # 층별 중앙값 4개
baseline_mae = (y_val - median).abs().mean().item()
print("\n[기준 모델] 출력값:", median.tolist())
print("[기준 모델] 검증 MAE:", round(baseline_mae, 3))

# ----------------------------------------------------------------------
# 2-1. 정답 표준화 (SCALE_TARGET = True일 때)
#   모델은 '표준화된 두께'(평균 0, 표준편차 1 근처)를 맞히도록 배운다.
#   예측을 원래 두께로 되돌리는 식: 두께 = 모델출력 × y_std + y_mean
#   False면 y_mean = 0, y_std = 1이라 원래 방식과 똑같다.
# ----------------------------------------------------------------------
if SCALE_TARGET:
    y_mean = y_train.mean(dim=0)
    y_std = y_train.std(dim=0)
else:
    y_mean = torch.zeros(4)
    y_std = torch.ones(4)
y_train_fit = (y_train - y_mean) / y_std          # 모델이 학습에 쓰는 정답
print("정답 표준화:", SCALE_TARGET, "| 평균:", y_mean.tolist(), "| 표준편차:", y_std.tolist())

# ----------------------------------------------------------------------
# 3. 모델·손실·최적화 도구
# ----------------------------------------------------------------------
model = nn.Sequential(
    nn.Linear(226, HIDDEN), nn.ReLU(),
    nn.Linear(HIDDEN, HIDDEN), nn.ReLU(),
    nn.Linear(HIDDEN, HIDDEN), nn.ReLU(),
    nn.Linear(HIDDEN, 4),
)
loss_fn = nn.L1Loss()                                   # MAE
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

# 학습률 스케줄러: 매 epoch 검증 MAE를 받아서, LR_PATIENCE epoch 동안 좋아지지 않으면
# 학습률 × 0.5. 처음엔 크게 움직이고, 정체되면 더 잘게 조정하게 만든다.
scheduler = None
if USE_LR_SCHEDULER:
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=LR_PATIENCE)


def evaluate(X, y):
    """검증 데이터 전체의 MAE(전체, 층별)를 계산한다. 가중치는 바꾸지 않는다."""
    model.eval()
    abs_err_sum = torch.zeros(4)
    with torch.no_grad():
        for start in range(0, len(X), 8192):
            pred = model(X[start:start + 8192]) * y_std + y_mean   # 원래 두께로 되돌림
            abs_err_sum += (pred - y[start:start + 8192]).abs().sum(dim=0)
    layer_mae = abs_err_sum / len(X)
    return layer_mae.mean().item(), layer_mae.tolist()


# ----------------------------------------------------------------------
# 4. 학습 반복
#    epoch 1번 = 학습 데이터 648,000개를 (섞어서) 한 바퀴 모두 사용
#    미니배치 1개 = 그중 1,024개로 예측 → 오차 → 기울기 → 가중치 1번 수정
# ----------------------------------------------------------------------
shuffle_gen = torch.Generator().manual_seed(TRAIN_SEED)
best_val_mae = float("inf")
best_epoch = 0
n_train = len(X_train)

# 이어하기: 학습이 중간에 꺼져도 다시 실행하면 멈춘 epoch 다음부터 계속한다.
#   매 epoch 끝에 '지금 상태 전부'(가중치, Adam 내부 값, 학습률, 섞기 난수 위치)를
#   _last.pt에 저장해 둔다. 그래서 끊기지 않고 학습한 것과 같은 결과가 나온다.
last_path = result_dir / f"mlp_seed{TRAIN_SEED}{tag}_last.pt"
start_epoch = 1
if last_path.exists():
    state = torch.load(last_path)
    model.load_state_dict(state["model"])
    optimizer.load_state_dict(state["optimizer"])
    if scheduler is not None:
        scheduler.load_state_dict(state["scheduler"])
    shuffle_gen.set_state(state["shuffle_gen"])
    best_val_mae, best_epoch = state["best_val_mae"], state["best_epoch"]
    start_epoch = state["epoch"] + 1
    print(f"\n[이어하기] epoch {state['epoch']}까지 끝난 상태에서 계속합니다. "
          f"(지금까지 최저 검증 MAE {best_val_mae:.3f}, epoch {best_epoch})")

print(f"\n{'epoch':>5} | {'학습 MAE':>9} | {'검증 MAE':>9} | 층별 검증 MAE (1~4) | 시간")
for epoch in range(start_epoch, MAX_EPOCHS + 1):
    if epoch - 1 - best_epoch >= PATIENCE:      # 이미 조기 종료 조건을 채운 상태로 이어한 경우
        break
    t0 = time.time()
    model.train()
    order = torch.randperm(n_train, generator=shuffle_gen)   # 매 epoch 새로 섞기
    loss_sum = 0.0

    for start in range(0, n_train, BATCH_SIZE):
        batch = order[start:start + BATCH_SIZE]
        X_batch, y_batch = X_train[batch], y_train_fit[batch]

        optimizer.zero_grad()                 # 이전 기울기 지우기
        pred = model(X_batch)
        loss = loss_fn(pred, y_batch)
        loss.backward()                       # 기울기 계산
        optimizer.step()                      # 가중치 수정

        # 기록용: 원래 두께 단위의 MAE (학습에는 영향 없음)
        with torch.no_grad():
            raw_mae = ((pred - y_batch).abs() * y_std).mean()
        loss_sum += raw_mae.item() * len(batch)

    train_mae = loss_sum / n_train
    val_mae, val_layer = evaluate(X_val, y_val)
    current_lr = optimizer.param_groups[0]["lr"]      # 이번 epoch에 쓴 학습률
    if scheduler is not None:
        scheduler.step(val_mae)                       # 다음 epoch 학습률 결정

    mark = ""
    if val_mae < best_val_mae:                # 검증 MAE가 가장 좋으면 저장
        best_val_mae, best_epoch = val_mae, epoch
        torch.save({"model": model.state_dict(), "y_mean": y_mean, "y_std": y_std,
                    "epoch": epoch, "val_mae": val_mae, "hidden": HIDDEN}, best_model_path)
        mark = " *저장"

    layer_text = " ".join(f"{v:6.2f}" for v in val_layer)
    print(f"{epoch:5d} | {train_mae:9.3f} | {val_mae:9.3f} | {layer_text} | "
          f"{time.time() - t0:4.1f}s | lr {current_lr:.1e}{mark}", flush=True)

    # 이어하기용 상태 저장 (임시 파일에 쓴 뒤 이름을 바꿔서, 저장 도중 꺼져도 파일이 깨지지 않게 함)
    tmp_path = last_path.with_suffix(".tmp")
    torch.save({"model": model.state_dict(), "optimizer": optimizer.state_dict(),
                "scheduler": scheduler.state_dict() if scheduler is not None else None,
                "shuffle_gen": shuffle_gen.get_state(), "best_val_mae": best_val_mae,
                "best_epoch": best_epoch, "epoch": epoch}, tmp_path)
    tmp_path.replace(last_path)

    if epoch - best_epoch >= PATIENCE:
        print(f"검증 MAE가 {PATIENCE} epoch 동안 좋아지지 않아 학습을 멈춥니다.")
        break

print(f"\n가장 좋은 검증 MAE: {best_val_mae:.3f} (epoch {best_epoch})")
print(f"기준 모델 대비: {baseline_mae:.3f} → {best_val_mae:.3f}")
print("저장 위치:", best_model_path)
