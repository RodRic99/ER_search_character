# AWS 배포와 RDS 이전 가이드

이 프로젝트는 현재 `Next.js` 프론트엔드, `Spring Boot` 백엔드, `FastAPI` 예측 API, `MySQL` 데이터베이스로 구성되어 있습니다.

AWS에서는 두 가지 방식으로 운영할 수 있습니다.

- 빠른 시작: [compose.aws.yaml](/C:/Users/wnsgu/OneDrive/바탕%20화면/CapStone/ER_search_character/compose.aws.yaml)로 EC2 한 대에 `mysql`까지 함께 실행
- 운영 권장: [compose.aws.rds.yaml](/C:/Users/wnsgu/OneDrive/바탕%20화면/CapStone/ER_search_character/compose.aws.rds.yaml)로 애플리케이션만 띄우고, DB는 Amazon RDS MySQL 사용

지금 단계에서는 두 번째 방식을 권장합니다. 프론트는 이미 AWS에 올라가 있고, 이후 `get_user` 수집/학습 파이프라인까지 AWS 쪽으로 옮기기 쉬워집니다.

## 추천 구조

- Frontend: Next.js
- Backend: Spring Boot
- Predict API: FastAPI
- Database: Amazon RDS for MySQL
- Reverse proxy: Nginx

## 준비물

- RDS MySQL 인스턴스
- EC2 또는 기존 애플리케이션 서버
- RDS 보안 그룹
  - 백엔드/FastAPI가 있는 서버에서만 `3306` 접근 허용
  - 가능하면 `Public Access = No`

## 1. RDS 생성

권장 기본값:

- Engine: MySQL 8.x
- Region: `ap-northeast-2` (서울)
- DB name: `er_search_character`
- App user: `er_app`
- Public access: `No`
- Backup retention: 최소 7일

주의:

- 운영 DB 비밀번호는 절대 Git에 넣지 않습니다.
- RDS endpoint는 `.env.aws.rds`에만 넣습니다.

## 2. 로컬 DB 덤프 생성

스크립트:

- [export-local-db.ps1](/C:/Users/wnsgu/OneDrive/바탕%20화면/CapStone/ER_search_character/deployment/aws/export-local-db.ps1)

예시:

```powershell
powershell -ExecutionPolicy Bypass -File .\deployment\aws\export-local-db.ps1 `
  -Database er_search_character `
  -User root `
  -Password "YOUR_LOCAL_DB_PASSWORD"
```

결과 파일은 기본적으로 아래에 생성됩니다.

- [deployment/aws/tmp/local-db-export.sql.zip](/C:/Users/wnsgu/OneDrive/바탕%20화면/CapStone/ER_search_character/deployment/aws/tmp/local-db-export.sql.zip)

## 3. RDS로 import

스크립트:

- [import-rds-dump.ps1](/C:/Users/wnsgu/OneDrive/바탕%20화면/CapStone/ER_search_character/deployment/aws/import-rds-dump.ps1)

예시:

```powershell
powershell -ExecutionPolicy Bypass -File .\deployment\aws\import-rds-dump.ps1 `
  -RdsHost "your-rds-endpoint.ap-northeast-2.rds.amazonaws.com" `
  -Database er_search_character `
  -User er_app `
  -Password "YOUR_RDS_PASSWORD" `
  -DumpPath ".\deployment\aws\tmp\local-db-export.sql.zip"
```

### EC2를 경유해서 import하는 경우

로컬 PC에서 직접 RDS에 붙지 않고, EC2에서 RDS로 import하는 방식입니다.

업로드 스크립트:

- [upload-db-dump-to-ec2.ps1](/C:/Users/wnsgu/OneDrive/바탕%20화면/CapStone/ER_search_character/deployment/aws/upload-db-dump-to-ec2.ps1)

EC2 실행 스크립트:

- [import-rds-from-ec2.sh](/C:/Users/wnsgu/OneDrive/바탕%20화면/CapStone/ER_search_character/deployment/aws/import-rds-from-ec2.sh)

1. 로컬 dump 파일을 EC2로 올립니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\deployment\aws\upload-db-dump-to-ec2.ps1 `
  -PemPath ".\er-search-key.pem" `
  -Ec2Host "YOUR_EC2_PUBLIC_IP_OR_DNS" `
  -Ec2User "ubuntu" `
  -LocalDumpPath ".\deployment\aws\tmp\local-db-export.sql.zip"
```

2. EC2에 접속합니다.

```bash
ssh -i er-search-key.pem ubuntu@YOUR_EC2_PUBLIC_IP_OR_DNS
```

3. import 스크립트를 EC2로 올리거나 내용을 붙여넣어 실행합니다.

```bash
chmod +x import-rds-from-ec2.sh
./import-rds-from-ec2.sh \
  "your-rds-endpoint.ap-northeast-2.rds.amazonaws.com" \
  "3306" \
  "er_search_character" \
  "er_app" \
  "YOUR_RDS_PASSWORD" \
  "~/er_migration/local-db-export.sql.zip"
```

이 방식의 장점:

- RDS를 퍼블릭으로 열 필요가 없음
- RDS 보안 그룹에서 EC2 보안 그룹만 허용하면 됨
- 대용량 import가 더 안정적임

## 4. RDS 연결 확인

스크립트:

- [verify-rds-connection.ps1](/C:/Users/wnsgu/OneDrive/바탕%20화면/CapStone/ER_search_character/deployment/aws/verify-rds-connection.ps1)

예시:

```powershell
powershell -ExecutionPolicy Bypass -File .\deployment\aws\verify-rds-connection.ps1 `
  -RdsHost "your-rds-endpoint.ap-northeast-2.rds.amazonaws.com" `
  -Database er_search_character `
  -User er_app `
  -Password "YOUR_RDS_PASSWORD"
```

이 스크립트는 다음을 확인합니다.

- 기본 접속 가능 여부
- 주요 테이블 row 수
- `rankdb_v2`, `rankdb_train_base`, `daily_position_synergy_cache`, `daily_score_metric_cache` 존재 여부

## 5. AWS 애플리케이션 서버 설정

RDS용 환경 파일 생성:

```powershell
Copy-Item .env.aws.rds.example .env.aws.rds
```

필수 수정값:

- `RDS_HOST`
- `RDS_PORT`
- `RDS_DATABASE`
- `RDS_USERNAME`
- `RDS_PASSWORD`
- `BSER_API_KEY`
- `NEXT_PUBLIC_API_BASE_URL`
- `APP_CORS_ALLOWED_ORIGINS`

## 6. 애플리케이션 실행

RDS를 쓸 때는 `mysql` 컨테이너를 띄우지 않고 아래 compose만 사용합니다.

```bash
docker compose --env-file .env.aws.rds -f compose.aws.rds.yaml up -d --build
```

상태 확인:

```bash
docker compose --env-file .env.aws.rds -f compose.aws.rds.yaml ps
docker compose --env-file .env.aws.rds -f compose.aws.rds.yaml logs -f backend
docker compose --env-file .env.aws.rds -f compose.aws.rds.yaml logs -f predict-api
```

## 7. 수집/학습 파이프라인

현재 로컬 Windows에서 돌고 있는 스크립트도 `.env`의 DB 설정만 RDS로 바꾸면 그대로 사용할 수 있습니다.

관련 파일:

- [eternareturn_DB/Get_User_data_py.py](/C:/Users/wnsgu/OneDrive/바탕%20화면/CapStone/ER_search_character/eternareturn_DB/Get_User_data_py.py)
- [eternareturn_DB/daily_rank_pipeline.py](/C:/Users/wnsgu/OneDrive/바탕%20화면/CapStone/ER_search_character/eternareturn_DB/daily_rank_pipeline.py)

즉 이전 직후에도:

- 6시간마다 `get_user` 수집
- 00시 기준 배치 학습/예측

구조는 그대로 유지할 수 있습니다.

## 롤백 방법

RDS 전환이 잘 안 되면 애플리케이션만 다시 로컬 MySQL 모드로 되돌리면 됩니다.

```bash
docker compose --env-file .env.aws -f compose.aws.yaml up -d --build
```

## 체크리스트

- [ ] RDS endpoint 확인
- [ ] RDS 보안 그룹에서 애플리케이션 서버만 3306 허용
- [ ] 로컬 dump 생성
- [ ] RDS import 완료
- [ ] `verify-rds-connection.ps1` 통과
- [ ] `.env.aws.rds` 설정 완료
- [ ] `compose.aws.rds.yaml`로 앱 실행
- [ ] 백엔드 `/api/player-stats/simulate` 정상 응답 확인
