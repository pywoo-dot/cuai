import pandas as pd
from pathlib import Path

# 이 파이썬 파일을 기준으로 데이터 위치 지정
data_path = Path(__file__).parent / "원본데이터" / "train.csv"

# 첫 5행만 읽기
data = pd.read_csv(data_path, nrows=5)

print("읽은 데이터의 크기:", data.shape)
print(data.head())

# 입력: 반사율 226개
input_columns = [str(i) for i in range(226)]
X = data[input_columns]

# 정답: 각 층의 두께 4개
target_columns = ["layer_1", "layer_2", "layer_3", "layer_4"]
y = data[target_columns]

print("\n입력 X의 크기:", X.shape)
print("정답 y의 크기:", y.shape)
