# Spot Training Checklist

이 체크리스트는 `daily_rank_pipeline.py`를 EC2 Spot 인스턴스에서 일일 학습 배치로 돌릴 때 필요한 최소 단계를 정리합니다.

## 1. 준비 상태

- RDS 접속 가능
- Git 저장소 clone 가능한 URL 준비
- S3 버킷 생성 완료
- Spot 인스턴스용 IAM Role 생성 완료

## 2. IAM Role

아래 권한이 필요합니다.

- S3 `ListBucket`
- S3 `GetObject`
- S3 `PutObject`

예시 정책:

- `deployment/aws/iam-spot-training-s3-policy.json`

## 3. 환경변수

기본 예시:

- `deployment/aws/.env.spot-training.example`

필수 값:

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `AWS_REGION`
- `TRAINING_ARTIFACT_BUCKET`
- `TRAINING_ARTIFACT_PREFIX`
- `TRAINING_XGB_DEVICE=cpu`

## 4. Spot 인스턴스 내부 실행 방식

핵심 실행 스크립트:

- `deployment/aws/run-spot-training.sh`

기본 동작:

1. Python 의존성 설치
2. `daily_rank_pipeline.py --run-date ...` 실행
3. 모델/CSV/summary 생성
4. S3 업로드

기본 권장값:

- `TRAINING_XGB_DEVICE=cpu`

## 5. 완전 자동 부팅 방식

User data 스크립트:

- `deployment/aws/spot-training-user-data.sh`

이 스크립트는 다음 흐름을 가정합니다.

1. 인스턴스 부팅
2. git clone
3. 학습 실행
4. 종료

필수 환경변수:

- `REPO_URL`
- `.env.spot-training.example`의 값들

## 6. 권장 운영 구조

- Vercel: 프론트
- EC2 On-Demand: `nginx + backend + predict-api`
- RDS: 운영 DB
- EC2 Spot: 학습 전용
- S3: 모델/예측 결과/summary 저장

## 7. 학습 완료 후 서비스 반영

상시 EC2에서 아래 스크립트를 실행하면 됩니다.

- `deployment/aws/refresh-predict-api.sh`

이 스크립트는:

1. S3의 최신 manifest 확인
2. 최신 모델 다운로드
3. `predict-api` 재시작

## 8. 첫 실행 추천 순서

1. S3 버킷 생성
2. IAM Role 생성
3. Spot 인스턴스 생성
4. `.env.spot-training.example` 값 채우기
5. `run-spot-training.sh` 수동 1회 실행
6. S3 업로드 확인
7. 상시 EC2에서 `refresh-predict-api.sh` 실행
8. 정상 확인 후 EventBridge Scheduler 연결

## 9. 다음 자동화 단계

초기에는 EventBridge + Launch Template 조합이 가장 단순합니다.

추후 확장 후보:

- AWS Batch
- ECS Scheduled Task

## 10. CPU Spot 권장 시작 스펙

- AMI: Amazon Linux
- 구매 옵션: Spot
- 인스턴스 타입 후보:
  - `c6i.large`
  - `c6a.large`
  - `m6i.large`
- 스토리지: 30~50GB
- IAM Instance Profile: `ERMetaSpotTrainingRole`
- 보안 그룹: SSH `22`만 내 IP 허용
