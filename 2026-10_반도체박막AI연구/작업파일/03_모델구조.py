import torch
from torch import nn

# 다시 실행해도 같은 초기 가중치로 시작하도록 설정
torch.manual_seed(42)

# MLP 구조 만들기
model = nn.Sequential(
    nn.Linear(226, 160),
    nn.ReLU(),

    nn.Linear(160, 160),
    nn.ReLU(),

    nn.Linear(160, 160),
    nn.ReLU(),

    nn.Linear(160, 4)
)

print("모델 구조:")
print(model)

# 구조 확인용 가짜 입력: 표본 5개 × 반사율 226개
example_input = torch.zeros(5, 226)

# 입력을 모델에 통과시키기
with torch.no_grad():
    prediction = model(example_input)

print("\n입력 크기:", example_input.shape)
print("출력 크기:", prediction.shape)
print("\n학습 전 출력값:")
print(prediction)