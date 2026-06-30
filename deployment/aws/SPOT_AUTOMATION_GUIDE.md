# Spot Automation Guide

`Launch Template + EC2 Spot + EventBridge Scheduler` 기준으로 `collector -> training -> shutdown` 자동화를 구성하는 안내입니다.

## 1. Launch Template 권장값

- Name: `ermeta-spot-training-template`
- AMI: `Amazon Linux 2023`
- Instance type: `m6i.xlarge`
- Purchase option: `Spot`
- Request type: `one-time`
- Interruption behavior: `terminate`
- IAM instance profile: `ERMetaSpotTrainingRole`
- Storage: `50GB gp3`
- Security group: `ermeta_spot_training_sg`
  - inbound: `22/tcp` from your IP only
- Auto-assign public IP: `Enable`

## 2. User data에 넣을 스크립트

Launch Template의 user data에는 아래 파일 내용을 그대로 넣습니다.

- `deployment/aws/spot-training-user-data.sh`

이 스크립트는 아래 순서로 동작합니다.

1. 패키지 설치
2. GitHub repo clone/pull
3. `.env.collector` 생성
4. `.env.spot-training` 생성
5. `run-rankdb-collector.sh` 실행
6. `run-spot-training.sh` 실행
7. 작업 종료 후 인스턴스 종료

## 3. User data에 같이 넘길 환경변수

최소 필수 값:

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `API_KEY`
- `AWS_REGION`
- `TRAINING_ARTIFACT_BUCKET`
- `TRAINING_ARTIFACT_PREFIX`

권장 값:

- `TRAINING_XGB_DEVICE=cpu`
- `TRAINING_RECENT_DAYS=7`
- `TRAINING_MEDIUM_DAYS=14`
- `TRAINING_MAX_AGE_DAYS=14`
- `TRAINING_RANKPOINT_THRESHOLD=6100`
- `TRAINING_BELOW_THRESHOLD_MAX_ROWS=80000`
- `TRAINING_RECENT_MAX_ROWS=120000`
- `TRAINING_MEDIUM_MAX_ROWS=80000`

선택 값:

- `RUN_COLLECTOR_FIRST=true`
- `RUN_TRAINING=true`
- `AUTO_SHUTDOWN=true`
- `RUN_DATE=YYYY-MM-DD`
- `REPO_URL`
- `REPO_BRANCH`

## 4. EventBridge Scheduler

권장 스케줄 예시:

- 매일 `00:10` 수집 + 학습 시작

대상:

- `EC2 RunInstances`
- 위 Launch Template 사용

즉 EventBridge는 “새 Spot 인스턴스를 실행”만 담당하고, 실제 수집/학습/종료는 user data가 담당합니다.

## 5. 로그 확인 위치

인스턴스 안에서:

- `/var/log/er-training/user-data.log`
- `/home/ec2-user/ER_search_character/eternareturn_DB/logs/`

## 6. 학습 완료 확인

- RDS
  - `rankdb_train_base`
  - `daily_position_synergy_cache`
  - `daily_score_metric_cache`
- S3
  - `s3://<bucket>/<prefix>/`
  - `latest/latest_training_manifest.json`

## 7. 운영 팁

- 수집과 학습을 같은 Spot에서 먼저 묶고, 이후 필요하면 분리합니다.
- 메모리 병목이 보이면 `m6i.xlarge`를 기본값으로 유지합니다.
- 현재 파이프라인은 최근 14일과 샘플링 제한을 기본으로 사용하도록 맞춰두는 편이 안전합니다.
