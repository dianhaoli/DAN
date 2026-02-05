# DAN FastAPI Backend

A production-ready FastAPI backend for the Digital Accountability Network (DAN) productivity tracking application.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   FastAPI    │────▶│  PostgreSQL │
│  (Next.js)  │     │   Backend    │     │  (Supabase) │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌─────────┐   ┌─────────┐
              │  Redis  │   │ Celery  │
              │ (Cache) │   │ Workers │
              └─────────┘   └─────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              ┌─────────┐  ┌─────────┐  ┌─────────┐
              │   ML    │  │ OpenAI  │  │  Stats  │
              │ Models  │  │   API   │  │  Jobs   │
              └─────────┘  └─────────┘  └─────────┘
```

## Features

- **Async ML Inference**: DistilBERT + XGBoost predictions run in background workers
- **AI Integration**: OpenAI for summaries, task breakdown, and insights
- **Rate Limiting**: Redis-based sliding window rate limiting
- **Background Jobs**: Celery workers for ML, AI, and stats aggregation
- **Firebase Auth**: Token verification middleware
- **Privacy Controls**: User visibility settings enforced in API

## Quick Start

### Prerequisites

- Python 3.11+
- Redis
- PostgreSQL (Supabase recommended)
- Firebase project (for authentication)

### Local Development

1. **Clone and install dependencies**

```bash
cd backend_fastapi
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

2. **Configure environment**

```bash
cp env.example .env
# Edit .env with your credentials
```

3. **Copy ML models**

```bash
mkdir -p ml_models
cp -r ../backend/src/distilbert-model ml_models/
cp ../backend/src/xgboost_productivity.json ml_models/
```

4. **Run database migrations**

```bash
alembic upgrade head
```

5. **Start Redis** (using Docker)

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

6. **Start the API server**

```bash
uvicorn app.main:app --reload --port 8000
```

7. **Start Celery workers** (in separate terminals)

```bash
# ML worker
celery -A celery_worker.celery_app worker --loglevel=info --queues=ml

# AI worker
celery -A celery_worker.celery_app worker --loglevel=info --queues=ai

# Stats worker
celery -A celery_worker.celery_app worker --loglevel=info --queues=stats
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Run migrations
docker-compose exec api alembic upgrade head
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/auth/verify` - Verify Firebase token
- `GET /api/auth/me` - Get current user

### Sessions
- `POST /api/sessions` - Create session (triggers async ML)
- `GET /api/sessions` - List sessions
- `GET /api/sessions/{id}` - Get session
- `PATCH /api/sessions/{id}` - Update session
- `DELETE /api/sessions/{id}` - Delete session

### Users
- `GET /api/users/{id}` - Get user (with privacy checks)
- `PATCH /api/users/{id}` - Update user
- `GET /api/users/{id}/stats` - Get user stats
- `GET /api/users/search` - Search users

### Todos
- `POST /api/todos` - Create todo
- `GET /api/todos` - List todos
- `POST /api/todos/{id}/complete` - Complete todo

### Social
- `POST /api/friends/request` - Send friend request
- `GET /api/friends` - List friends
- `GET /api/activities` - Get activity feed

### AI (Rate Limited)
- `POST /api/ai/summarize-session` - Generate session summary
- `POST /api/ai/breakdown-task` - Break down task into subtasks
- `POST /api/ai/insights` - Generate productivity insights

### Gamification
- `GET /api/badges` - List badges
- `GET /api/badges/user/{id}` - Get user's badges
- `GET /api/leaderboards` - List leaderboards

## ML Models

The backend uses two ML models:

1. **DistilBERT** - Text classification for activity labeling
   - Labels: study, distraction, research
   - Input: Page titles/URLs

2. **XGBoost** - Productivity score prediction
   - Output: 0-100 score
   - Features: clicks, keystrokes, time_on_page, activity_label

Models are preloaded at startup and inference runs in a thread pool.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `REDIS_URL` | Redis connection string | Yes |
| `FIREBASE_PROJECT_ID` | Firebase project ID | Yes |
| `FIREBASE_CREDENTIALS_PATH` | Path to service account JSON | No |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `OPENAI_MODEL` | OpenAI model (default: gpt-4) | No |
| `ML_MODELS_PATH` | Path to ML models directory | No |
| `RATE_LIMIT_GENERAL` | General rate limit (req/min) | No |
| `RATE_LIMIT_AI` | AI endpoint rate limit (req/hour) | No |

## Deployment

### Render

Use the provided `render.yaml` blueprint:

```bash
# Link to Render
render blueprint sync
```

### Manual Deployment

1. Build Docker image
2. Push to container registry
3. Deploy with environment variables
4. Run migrations: `alembic upgrade head`

## Project Structure

```
backend_fastapi/
├── app/
│   ├── api/            # HTTP routes
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   ├── workers/        # Celery tasks
│   ├── ml/             # ML inference
│   ├── ai/             # OpenAI integration
│   ├── middleware/     # Auth & rate limiting
│   └── utils/          # Helpers
├── migrations/         # Alembic migrations
├── ml_models/          # Trained models
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── render.yaml
```

## License

MIT
