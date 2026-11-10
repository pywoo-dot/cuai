# 팀원모델

팀원 각자의 모델 코드와 결과를 두는 곳입니다. 한 사람당 폴더 하나를 씁니다.

```
팀원모델/
  박영우/      → MLP는 작업파일/05_모델학습.py, 06_잡음평가.py 에 있음
  홍길동/
    README.md      어떤 모델인지, 실행 방법, 결과 요약
    train.py       학습 코드
    evaluate.py    공통평가.py 로 평가하는 코드
    결과/          평가 CSV, 학습 로그
```

## 지켜 주세요

- 자기 폴더만 수정합니다. 공통 파일(`작업파일/공통분할/`, `작업파일/공통평가.py`)을 바꿔야 하면 팀 단톡방에 먼저 이야기합니다.
- 데이터 분할은 `작업파일/공통분할/split_indices.npz`를 그대로 씁니다. 따로 나누지 않습니다.
- 최종평가(test) 분할은 팀이 확정할 때까지 쓰지 않습니다.
- 원본 CSV와 50MB가 넘는 파일(큰 모델 파일 등)은 올리지 않습니다.

## 자기 폴더에서 공통평가 쓰기

`공통평가.py`는 `작업파일` 폴더에 있습니다. 내 폴더의 코드에서 불러오려면 경로를 추가합니다.

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "작업파일"))

from 공통평가 import load_split, evaluate

X_train, y_train = load_split("train")   # 학습용
X_val, y_val = load_split("val")         # 검증용

# ... 모델 학습 ...

evaluate(my_predict, model_name="홍길동_RandomForest", split="val", train_seed=0)
```

평가 결과 CSV는 `작업파일/결과/`에 저장됩니다. 필요하면 자기 폴더의 `결과/`로 옮겨 올려 주세요.
