# AWS 배포 및 비용 계산 가이드

이 프로젝트는 `Next.js` 프론트엔드, `Spring Boot` 백엔드, `FastAPI` 예측 API, `MySQL`로 구성되어 있습니다. 발표/캡스톤 용도라면 한 대의 AWS 서버에서 Docker Compose로 실행하는 구성이 가장 단순하고 비용 계산도 쉽습니다.

## 추천 구성

### 저비용 배포

- Amazon Lightsail 또는 EC2 1대
- Docker Compose로 `frontend`, `backend`, `predict-api`, `mysql` 실행
- 고정 IP 1개
- 필요 시 도메인과 HTTPS는 나중에 추가

이 방식은 운영 편의성은 낮지만 서비스 수가 적어서 비용 설명이 쉽습니다.

### 운영형 배포

- AWS Amplify Hosting: Next.js 프론트엔드
- Elastic Beanstalk 또는 ECS/Fargate: Spring Boot 백엔드
- Elastic Beanstalk 또는 ECS/Fargate: FastAPI 예측 API
- Amazon RDS for MySQL: DB
- S3: CSV, 모델, 백업 파일 저장

이 방식은 안정적이지만 비용 항목이 많아집니다.

## AWS Pricing Calculator 입력 항목

[AWS Pricing Calculator](https://calculator.aws/#/)에서 아래 항목을 추가하면 됩니다.

### 저비용 배포 계산

1. `Amazon Lightsail` 또는 `Amazon EC2`
   - Region: `Asia Pacific (Seoul)` 또는 실제 배포 리전
   - Instance: 최소 `2 vCPU / 4 GB RAM` 권장
   - Hours: `730 hours/month`
   - Storage: `40 GB` 이상
2. `Data Transfer`
   - 예상 월 방문자가 적으면 `10~50 GB/month`부터 입력
3. 선택: `Amazon Route 53`
   - 도메인을 AWS에서 관리할 경우 Hosted Zone 1개

### 운영형 배포 계산

1. `AWS Amplify Hosting`
   - Build minutes/month
   - Stored data GB
   - Data transfer out GB
2. `Amazon EC2` 또는 `AWS Elastic Beanstalk`
   - Spring Boot 백엔드용 인스턴스
   - FastAPI 예측 API용 인스턴스
3. `Amazon RDS for MySQL`
   - Single-AZ
   - 작은 인스턴스부터 시작
   - Storage 20 GB 이상
4. `Amazon S3`
   - 모델 파일, CSV, 로그 백업 용량
5. 선택: `Elastic Load Balancing`, `CloudWatch`, `Route 53`

AWS 공식 문서 기준으로 Pricing Calculator는 비용 예측용 도구이며 실제 비용은 사용량에 따라 달라집니다. Elastic Beanstalk 자체는 추가 요금이 없고 생성된 EC2, S3, Load Balancer 같은 리소스 요금이 청구됩니다. RDS는 사용한 인스턴스 시간, 스토리지, 백업, 데이터 전송량에 따라 비용이 생깁니다.

## 배포 순서

### 1. 서버 만들기

Lightsail 또는 EC2 Ubuntu 서버를 생성합니다.

보안 그룹 또는 방화벽:

- SSH: `22`
- 프론트엔드: `3000`
- 백엔드 API: `8080`
- 예측 API `8000`과 MySQL `3306`은 외부 공개하지 않는 것을 권장합니다. 현재 Compose 파일도 두 포트를 외부에 공개하지 않습니다.

### 2. 서버에 Docker 설치

Ubuntu 기준:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin git
sudo usermod -aG docker ubuntu
```

로그아웃 후 다시 접속합니다.

### 3. 프로젝트 업로드

GitHub를 사용한다면:

```bash
git clone YOUR_REPOSITORY_URL
cd ER_search_character
```

직접 업로드한다면 프로젝트 폴더 전체를 서버로 복사합니다.

### 4. 환경 변수 설정

```bash
cp .env.aws.example .env.aws
nano .env.aws
```

반드시 수정할 값:

- `MYSQL_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `BSER_API_KEY`
- `NEXT_PUBLIC_API_BASE_URL`
- `APP_CORS_ALLOWED_ORIGINS`

예시:

```env
NEXT_PUBLIC_API_BASE_URL=http://13.124.10.20:8080
APP_CORS_ALLOWED_ORIGINS=http://13.124.10.20:3000
```

### 5. 실행

```bash
docker compose --env-file .env.aws -f compose.aws.yaml up -d --build
```

상태 확인:

```bash
docker compose --env-file .env.aws -f compose.aws.yaml ps
docker compose --env-file .env.aws -f compose.aws.yaml logs -f backend
```

접속:

- 프론트엔드: `http://YOUR_SERVER_PUBLIC_IP:3000`
- 백엔드 API: `http://YOUR_SERVER_PUBLIC_IP:8080/api/tier-list`

## 주의할 점

- `NEXT_PUBLIC_API_BASE_URL`은 Next.js 빌드 시점에 들어갑니다. 서버 IP나 도메인을 바꾸면 프론트엔드 이미지를 다시 빌드해야 합니다.
- MySQL 초기 스키마는 `eternareturn_DB/schema_rankdb.sql`로 생성됩니다. 실제 서비스 데이터가 필요하면 별도 import가 필요합니다.
- `eternareturn_DB/.env`에는 로컬 비밀값이 들어갈 수 있으니 GitHub 공개 저장소에 올리지 않는 것이 좋습니다.
- 비용 폭주를 막으려면 AWS Budgets에서 월 예산 알림을 꼭 설정하세요.

## 공식 참고 링크

- [AWS Pricing Calculator](https://calculator.aws/#/)
- [AWS Pricing Calculator 문서](https://docs.aws.amazon.com/cost-management/latest/userguide/pricing-calculator.html)
- [Elastic Beanstalk 요금](https://aws.amazon.com/ko/elasticbeanstalk/pricing/)
- [Amazon RDS 요금](https://aws.amazon.com/rds/pricing/)
- [AWS Amplify 요금](https://aws.amazon.com/jp/amplify/pricing/)
