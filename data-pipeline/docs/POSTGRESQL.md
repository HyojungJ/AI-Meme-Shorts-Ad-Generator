# Lightsail + PostgreSQL 외부 접속 설정 가이드

- 작업 기간: 2026.01.05
- 관련 이슈: #17

## 서버에 PostgreSQL 직접 설치 및 초기 설정

### 1. PostgreSQL 설치

```bash
sudo apt-get update
sudo apt install postgresql postgresql-contrib
```

### 2. 설치 확인

```bash
sudo systemctl status postgresql
sudo -u postgres psql -c "SELECT version();"
```

### 3. 계정 전환

```bash
sudo -i -u postgres
```

### 4. 비밀번호 변경

```bash
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'your_secure_password';"
```

---

## 5432 포트 외부 접속 허용

### 1. `postgresql.conf` 수정

- AWS Lightsail **네트워킹 방화벽**에서 **TCP 5432 허용**되어 있어야 함

```bash
sudo nano /etc/postgresql/14/main/postgresql.conf
```

```python
# conf 파일 내부에서 아래 설정 찾아 수정
#listen_addresses = 'localhost'
listen_addresses = '*'

```

### 2. `pg_hba.conf` 수정

```bash
sudo nano /etc/postgresql/14/main/pg_hba.conf
```

```bash
# 맨 아래에 추가
host    all     all     내_공인_IP/32     md5
```

### 3. PostgreSQL 재시작

```sql
sudo systemctl restart postgresql
```

### 4. 서버가 5432를 리스닝 중인지 확인

```bash
sudo ss -tulnp | grep 5432
# 정상이면, LISTEN 0 128 0.0.0.0:5432
```

---

## Database Setup

```
- Host: 퍼블릭 IPv4 주소 (Lightsail 인스턴스)
- Port: 5432
- Database: postgres
- Username: postgres
- Password: ********
```