opera-bridge/
├── src/
│   ├── main.py                          ← FastAPI app entry point
│   └── app/
│       ├── core/        config, logging (structlog), security (API key)
│       ├── clients/     opera_auth_client.py, opera_cloud_client.py
│       ├── db/          models.py (SQLAlchemy), session.py, 4 repositories
│       ├── schemas/     internal/ + opera/ DTOs (Pydantic)
│       ├── mappers/     reservation, room, guest mappers
│       ├── services/    reservation, room, guest, sync services
│       ├── middlewares/ request_logging (trace_id tự động)
│       ├── jobs/        room_status_sync.py
│       └── utils/       error_normalizer.py, retry.py (tenacity)
├── alembic/             env.py + migration 001 (toàn bộ 6 bảng + triggers)
├── tests/               test_mappers.py, test_health.py
├── Dockerfile
├── docker-compose.yml   (app + PostgreSQL)
├── requirements.txt
├── pyproject.toml       (pytest, ruff config)
└── .env.example



# 1. Sao chép cấu hình
cp .env.example .env
# Điền OPERA_CLIENT_ID, OPERA_CLIENT_SECRET, OPERA_BASE_URL, OPERA_HOTEL_ID

# 2. Chạy bằng Docker
wsl
cd opera-bridge
docker compose up --build

# Hoặc chạy local
pip install -r requirements.txt
alembic upgrade head
uvicorn src.main:app --reload

# 3. Chạy test
pytest
API docs tại http://localhost:8000/docs (chỉ khi APP_ENV != production).