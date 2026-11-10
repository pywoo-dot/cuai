import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split

data_path = Path(__file__).parent / "원본데이터" / "train.csv"

# 파일을 50,000행씩 읽고, 각 묶음에서 약 10%를 선택합니다.
selected_parts = []

for part in pd.read_csv(data_path, chunksize=50000):
    selected = part.sample(frac=0.1, random_state=42)
    selected_parts.append(selected)

    print("데이터를 읽는 중입니다...", len(selected_parts), "번째 묶음")

# 선택한 표본들을 하나의 표로 합칩니다.
data = pd.concat(selected_parts, ignore_index=True)

# 입력과 정답을 분리합니다.
input_columns = [str(i) for i in range(226)]
target_columns = ["layer_1", "layer_2", "layer_3", "layer_4"]

X = data[input_columns]
y = data[target_columns]

# 80%는 학습용, 20%는 나중에 다시 나눌 데이터로 분리합니다.
X_train, X_remaining, y_train, y_remaining = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

# 남은 20%를 반으로 나눠 검증용 10%, 최종 평가용 10%를 만듭니다.
X_val, X_test, y_val, y_test = train_test_split(
    X_remaining, y_remaining,
    test_size=0.5,
    random_state=42
)

print("\n선택한 전체 표본 수:", len(data))
print("학습용:", X_train.shape, y_train.shape)
print("검증용:", X_val.shape, y_val.shape)
print("최종 평가용:", X_test.shape, y_test.shape)

# 학습 데이터에서 채널별 평균과 표준편차를 계산합니다.
train_mean = X_train.mean()
train_std = X_train.std(ddof=0)

# 값이 전부 같은 채널이 있다면 0으로 나누지 않도록 처리합니다.
train_std = train_std.replace(0, 1)

# 세 데이터에 동일한 기준을 적용합니다.
X_train_scaled = (X_train - train_mean) / train_std
X_val_scaled = (X_val - train_mean) / train_std
X_test_scaled = (X_test - train_mean) / train_std

# 첫 번째 채널의 변환 결과를 확인합니다.
print("\n학습 데이터 첫 채널의 표준화 결과")
print("평균:", X_train_scaled["0"].mean())
print("표준편차:", X_train_scaled["0"].std(ddof=0))

import torch
from torch import nn

torch.manual_seed(42)

# 학습 데이터 중 첫 5개를 PyTorch용 숫자 배열로 변환
X_batch = torch.tensor(
    X_train_scaled.iloc[:5].to_numpy(),
    dtype=torch.float32
)

y_batch = torch.tensor(
    y_train.iloc[:5].to_numpy(),
    dtype=torch.float32
)

# 앞서 확인한 MLP 구조
model = nn.Sequential(
    nn.Linear(226, 160),
    nn.ReLU(),
    nn.Linear(160, 160),
    nn.ReLU(),
    nn.Linear(160, 160),
    nn.ReLU(),
    nn.Linear(160, 4)
)

# 평균 절대오차(MAE)를 계산할 도구
loss_fn = nn.L1Loss()

# 학습 전 예측과 오차 확인
with torch.no_grad():
    prediction = model(X_batch)
    loss = loss_fn(prediction, y_batch)

print("\n첫 번째 표본의 예측 두께:")
print(prediction[0])

print("\n첫 번째 표본의 정답 두께:")
print(y_batch[0])

print("\n5개 표본의 MAE:", loss.item())


# 가중치를 수정할 도구: Adam
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

model.train()
optimizer.zero_grad()

# 현재 가중치로 예측하고 오차 계산
prediction = model(X_batch)
loss_before = loss_fn(prediction, y_batch)

# 오차를 줄이기 위한 기울기 계산
loss_before.backward()

# 가중치를 실제로 한 번 수정
optimizer.step()

# 수정 후, 같은 표본에서 오차 다시 확인
with torch.no_grad():
    prediction_after = model(X_batch)
    loss_after = loss_fn(prediction_after, y_batch)

print("\n가중치 수정 전 MAE:", loss_before.item())
print("가중치 수정 후 MAE:", loss_after.item())
