# AWS Training Deployment

`daily_rank_pipeline.py`를 AWS에서 학습 배치로 운영할 때의 권장 구조입니다.

## 권장 아키텍처

- Vercel: 프론트엔드
- EC2 On-Demand: `nginx + Spring backend + predict-api`
- RDS MySQL: 운영 DB
- EC2 Spot: 학습/전체 조합 예측 배치
- S3: 모델/예측 CSV/summary 보관

## 필요한 환경변수

Spot 인스턴스에서 `eternareturn_DB/.env` 또는 셸 환경변수로 아래 값을 제공해야 합니다.

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `TRAINING_ARTIFACT_BUCKET`
- `TRAINING_ARTIFACT_PREFIX`
- `TRAINING_XGB_DEVICE=cpu`
- `AWS_REGION`

선택:

- `TRAINING_MODEL_SUFFIX`

## S3에 올라가는 산출물

`daily_rank_pipeline.py`는 실행이 끝나면 아래를 S3에 업로드합니다.

- `models/xgb_model_all_tiers.json`
- `models/xgb_model_all_tiers_features.csv`
- `models/xgb_model_all_tiers_label_encoders.json`
- 일일 summary JSON
- 학습 결과 CSV
- 전체 조합 예측 CSV
- 포지션 시너지 캐시 CSV
- 절대 점수 캐시 CSV
- `latest/latest_training_manifest.json`

## Spot 인스턴스 실행 순서

### 1. 최소 IAM 권한

Spot 인스턴스 역할에 아래 권한이 필요합니다.

- S3 `PutObject`
- S3 `GetObject`
- S3 `ListBucket`
- 필요하면 CloudWatch Logs

### 2. 실행 스크립트

Spot 인스턴스 내부에서:

```bash
chmod +x deployment/aws/run-spot-training.sh
./deployment/aws/run-spot-training.sh 2026-05-09
```

기본적으로:

- `requirements.txt` 설치
- `daily_rank_pipeline.py --run-date YYYY-MM-DD` 실행

을 수행합니다.

기본 권장값은 `TRAINING_XGB_DEVICE=cpu` 입니다.

### 3. User data로 완전 자동화

`deployment/aws/spot-training-user-data.sh`를 사용하면:

1. 인스턴스 부팅
2. repo clone
3. 학습 실행
4. 종료

까지 자동화할 수 있습니다.

필수 값:

- `REPO_URL`
- DB 환경변수들
- S3 환경변수들

### 4. 스케줄링 추천

초기 운영:

- EventBridge Scheduler
- Launch Template + Spot Instance
- 매일 00:10 실행

추후 확장:

- AWS Batch
- ECS Scheduled Task

### 5. 상시 EC2에 최신 모델 반영

Spot 학습이 끝나면 상시 EC2도 새 모델을 받아야 합니다.

준비된 스크립트:

- `deployment/aws/sync-latest-training-artifacts.py`
- `deployment/aws/refresh-predict-api.sh`

동작:

1. S3의 `latest/latest_training_manifest.json` 확인
2. 최신 모델 3종 다운로드
3. `predict-api` 컨테이너 재시작

예시:

```bash
export TRAINING_ARTIFACT_BUCKET=your-bucket
export TRAINING_ARTIFACT_PREFIX=er-training-prod
export AWS_REGION=ap-northeast-2

chmod +x deployment/aws/refresh-predict-api.sh
./deployment/aws/refresh-predict-api.sh
```

### 6. CPU Spot 권장 시작 스펙

- AMI: Amazon Linux
- 구매 옵션: Spot
- 인스턴스 타입 후보:
  - `c6i.large`
  - `c6a.large`
  - `m6i.large`
- 스토리지: 30~50GB
- IAM Instance Profile: `ERMetaSpotTrainingRole`
- 보안 그룹: SSH `22`만 내 IP 허용

## 운영 팁

- Spot은 중단될 수 있으므로 산출물은 로컬 디스크에만 두지 않습니다.
- 첫 운영은 GPU Spot이 아니라 CPU Spot에서 검증하는 편이 안전합니다.
- 상시 백엔드는 S3의 최신 manifest를 기준으로 새 모델을 내려받는 구조로 운영하면 안정적입니다.
